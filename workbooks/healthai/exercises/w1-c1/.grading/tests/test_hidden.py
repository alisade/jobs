"""Hidden tests for healthai/w1-c1."""

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from pydantic import TypeAdapter, ValidationError

from intake.app import app
from intake.clock import compute_deadline
from intake.models import PARequest

EST = timezone(timedelta(hours=-5))
EDT = timezone(timedelta(hours=-4))
UTCZ = timezone.utc
TA = TypeAdapter(PARequest)


def due(r):
    return datetime.fromisoformat(r.json()["decision_due"])


async def test_inpatient_standard_accepted(client, body):
    r = await client.post("/v1/pa-requests", json=body("inpatient"))
    assert r.status_code == 201, r.text
    assert r.json()["category"] == "inpatient"
    assert due(r) == datetime(2026, 11, 17, 15, 0, tzinfo=UTCZ)


@pytest.mark.parametrize("mutate", [
    lambda b: b.update(category="dental"),
    lambda b: b.update(drug_name="x" * 5),          # extra field on imaging
    lambda b: b.update(member_id="100201"),
    lambda b: b.update(diagnosis_codes=[]),
    lambda b: b.update(diagnosis_codes=["5450"]),
    lambda b: b.update(diagnosis_codes=["M54.123456"]),
    lambda b: b.update(modality="ultrasound"),
])
async def test_imaging_validation_errors(client, body, mutate):
    b = body("imaging")
    mutate(b)
    assert (await client.post("/v1/pa-requests", json=b)).status_code == 422


@pytest.mark.parametrize("mutate", [
    lambda b: b.update(days_supply="56"),           # strict int
    lambda b: b.update(days_supply=400),
    lambda b: b.update(hcpcs_code="1745J"),
    lambda b: b.update(clinical_justification=""),  # expedited needs one
    lambda b: b.update(clinical_justification="urgent"),
    lambda b: b.update(admit_date="2026-11-12"),    # inpatient field on medication
])
async def test_medication_validation_errors(client, body, mutate):
    b = body("medication")
    mutate(b)
    assert (await client.post("/v1/pa-requests", json=b)).status_code == 422


def test_union_dispatches_on_category(body):
    for which, cls in (("imaging", "ImagingRequest"), ("medication", "MedicationRequest"), ("inpatient", "InpatientRequest")):
        assert type(TA.validate_python(body(which))).__name__ == cls


def test_diagnosis_codes_normalized(body):
    m = TA.validate_python(body("medication"))
    assert m.diagnosis_codes == ["K50.90"]
    b = body("imaging")
    b["diagnosis_codes"] = [" u07.1 "]
    assert TA.validate_python(b).diagnosis_codes == ["U07.1"]


def test_discriminator_error_names_category(body):
    b = body("imaging")
    b["category"] = "dental"
    with pytest.raises(ValidationError) as ei:
        TA.validate_python(b)
    assert "category" in str(ei.value) or "discriminator" in str(ei.value)


def test_clock_rejects_naive_and_unknown_priority():
    with pytest.raises(ValueError):
        compute_deadline(datetime(2026, 11, 10, 9, 0), "standard", "commercial")
    with pytest.raises(ValueError):
        compute_deadline(datetime(2026, 11, 10, 9, 0, tzinfo=UTCZ), "urgent", "commercial")


def test_clock_qhp_ffe_has_no_federal_clock():
    assert compute_deadline(datetime(2026, 11, 10, 9, 0, tzinfo=UTCZ), "expedited", "qhp-ffe") is None


def test_expedited_is_72_elapsed_hours_across_dst():
    got = compute_deadline(datetime(2026, 3, 7, 12, 0, tzinfo=EST), "expedited", "commercial", "America/New_York")
    assert got == datetime(2026, 3, 10, 17, 0, tzinfo=UTCZ)


def test_standard_keeps_local_time_across_spring_forward():
    got = compute_deadline(datetime(2026, 3, 5, 10, 0, tzinfo=EST), "standard", "commercial", "America/New_York")
    assert got == datetime(2026, 3, 12, 14, 0, tzinfo=UTCZ)  # 10:00 EDT


def test_standard_keeps_local_time_across_fall_back():
    got = compute_deadline(datetime(2026, 10, 29, 10, 0, tzinfo=EDT), "standard", "medicaid-mco", "America/New_York")
    assert got == datetime(2026, 11, 5, 15, 0, tzinfo=UTCZ)  # 10:00 EST


def test_standard_uses_plan_time_zone_not_sender_offset():
    # received 2026-03-05 23:30 Mountain = 2026-03-06 06:30 UTC; plan is in Chicago
    got = compute_deadline(datetime(2026, 3, 5, 23, 30, tzinfo=timezone(timedelta(hours=-7))), "standard",
                           "medicare-advantage", "America/Chicago")
    assert got == datetime(2026, 3, 13, 5, 30, tzinfo=UTCZ)  # 00:30 CDT on 03-13


def test_returned_deadline_is_aware_utc():
    got = compute_deadline(datetime(2026, 11, 10, 9, 0, tzinfo=EST), "standard", "commercial")
    assert got.utcoffset() == timedelta(0)


async def test_qhp_member_gets_no_clock(client, body):
    b = body("imaging")
    b["member_id"] = "M-100205"
    r = await client.post("/v1/pa-requests", json=b)
    assert r.status_code == 201 and r.json()["clock"] == "none" and r.json()["decision_due"] is None


async def test_inactive_member_routes_to_eligibility_review(client, body):
    b = body("imaging")
    b["member_id"] = "M-100203"
    r = await client.post("/v1/pa-requests", json=b)
    assert r.status_code == 201 and r.json()["route"] == "eligibility-review"


async def test_eligibility_timeout_returns_503(client, body, fake):
    fake.delay_s = 2.0
    async with asyncio.timeout(1.5):
        r = await client.post("/v1/pa-requests", json=body("imaging"))
    assert r.status_code == 503
    assert "eligibility" in r.json()["detail"]


async def test_idempotent_retry_returns_same_case(client, body, fake):
    h = {"Idempotency-Key": "k-2026-11-10-0001"}
    a = await client.post("/v1/pa-requests", json=body("imaging"), headers=h)
    b = await client.post("/v1/pa-requests", json=body("imaging"), headers=h)
    assert a.status_code == 201 and b.status_code in (200, 201)
    assert a.json()["case_id"] == b.json()["case_id"]
    assert fake.calls == 1


async def test_idempotency_key_reuse_with_different_body_conflicts(client, body):
    h = {"Idempotency-Key": "k-2026-11-10-0002"}
    await client.post("/v1/pa-requests", json=body("imaging"), headers=h)
    other = body("imaging")
    other["body_region"] = "cervical spine"
    assert (await client.post("/v1/pa-requests", json=other, headers=h)).status_code == 409


async def test_without_key_each_post_is_a_new_case(client, body):
    a = await client.post("/v1/pa-requests", json=body("imaging"))
    b = await client.post("/v1/pa-requests", json=body("imaging"))
    assert a.json()["case_id"] != b.json()["case_id"]


async def test_unknown_case_404(client):
    assert (await client.get("/v1/pa-requests/PA-999999")).status_code == 404


async def test_lifespan_creates_and_closes_the_client():
    async with app.router.lifespan_context(app):
        cli = app.state.eligibility
        assert not cli.closed
    assert cli.closed


async def test_state_is_per_app_lifespan(body):
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            cid = (await c.post("/v1/pa-requests", json=body("imaging"))).json()["case_id"]
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            assert (await c.get(f"/v1/pa-requests/{cid}")).status_code == 404
