from datetime import datetime


async def test_imaging_standard_happy_path(client, body):
    r = await client.post("/v1/pa-requests", json=body("imaging"))
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["route"] == "clinical-review" and out["clock"] == "cms-0057-f"
    assert datetime.fromisoformat(out["decision_due"]) == datetime.fromisoformat("2026-11-17T19:30:00+00:00")
    got = await client.get(f"/v1/pa-requests/{out['case_id']}")
    assert got.status_code == 200 and got.json() == out


async def test_medication_expedited_is_accepted_with_72h_clock(client, body):
    r = await client.post("/v1/pa-requests", json=body("medication"))
    assert r.status_code == 201, r.text
    assert datetime.fromisoformat(r.json()["decision_due"]) == datetime.fromisoformat("2026-11-13T15:00:00+00:00")


async def test_naive_received_at_is_rejected(client, body):
    b = body("imaging")
    b["received_at"] = "2026-11-10T14:30:00"
    r = await client.post("/v1/pa-requests", json=b)
    assert r.status_code == 422
