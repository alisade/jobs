"""Hidden tests for healthai/w3-c1."""

from pathlib import Path

import pytest

from pas.bundle_check import problems, refs
from pas.mapper import X12Error, parse_x12, to_pas_bundle

FIX = Path(__file__).resolve().parent.parent / "fixtures"
CM = "http://hl7.org/fhir/sid/icd-10-cm"


def load(name):
    return to_pas_bundle((FIX / name).read_text())


def res(bundle, kind):
    return [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == kind]


def by_url(bundle):
    return {e["fullUrl"]: e["resource"] for e in bundle["entry"]}


def test_separators_come_from_isa():
    segs = parse_x12((FIX / "278_req_002.x12").read_text())
    assert segs[0][0] == "ISA" and segs[1][0] == "GS"
    assert ["HL", "4", "3", "EV", "0"] in segs
    assert all("\n" not in el for s in segs for el in s)


def test_parse_rejects_non_interchange():
    with pytest.raises(ValueError):
        parse_x12("GS*HI*X~ST*278*0001~")


def test_alternate_separators_bundle_is_valid():
    b, _ = load("278_req_002.x12")
    assert problems(b) == []


def test_all_references_resolve_and_are_urn_uuid():
    for name in ("278_req_001.x12", "278_req_002.x12"):
        b, _ = load(name)
        urls = by_url(b)
        assert all(u.startswith("urn:uuid:") for u in urls)
        for e in b["entry"]:
            for r in refs(e["resource"]):
                assert r in urls


def test_claim_points_at_the_right_resources():
    b, _ = load("278_req_001.x12")
    u = by_url(b)
    c = res(b, "Claim")[0]
    assert u[c["patient"]["reference"]]["resourceType"] == "Patient"
    assert u[c["provider"]["reference"]]["resourceType"] == "Practitioner"
    assert u[c["insurer"]["reference"]]["resourceType"] == "Organization"
    assert u[c["insurance"][0]["coverage"]["reference"]]["resourceType"] == "Coverage"
    assert c["insurance"][0]["focal"] is True


def test_multiple_diagnoses_principal_first_with_dots():
    b, _ = load("278_req_002.x12")
    u = by_url(b)
    c = res(b, "Claim")[0]
    codes = [u[d["diagnosisReference"]["reference"]]["code"]["coding"][0] for d in c["diagnosis"]]
    assert [x["code"] for x in codes] == ["I25.10", "E11.22", "Z95.5"]
    assert all(x["system"] == CM for x in codes)
    assert [d["sequence"] for d in c["diagnosis"]] == [1, 2, 3]


def test_dates_converted():
    b, _ = load("278_req_001.x12")
    c = res(b, "Claim")[0]
    assert c["created"] == "2026-11-10"
    assert c["item"][0]["servicedDate"] == "2026-11-18"
    p = res(b, "Patient")[0]
    assert p["birthDate"] == "1968-04-12" and p["gender"] == "male"


def test_rd8_period():
    b, _ = load("278_req_002.x12")
    assert res(b, "Claim")[0]["item"][0]["servicedPeriod"] == {"start": "2026-11-11", "end": "2026-11-13"}


def test_priority_from_level_of_service():
    s, _ = load("278_req_001.x12")
    e, w = load("278_req_002.x12")
    assert res(s, "Claim")[0]["priority"]["coding"][0]["code"] == "normal"
    assert res(e, "Claim")[0]["priority"]["coding"][0]["code"] == "stat"
    assert any("priority" in x.lower() or "level of service" in x.lower() for x in w)


def test_identifiers_and_systems():
    b, _ = load("278_req_001.x12")
    assert res(b, "Practitioner")[0]["identifier"][0] == {"system": "http://hl7.org/fhir/sid/us-npi", "value": "1999999984"}
    assert res(b, "Coverage")[0]["subscriberId"] == "M-100201"
    assert res(b, "Organization")[0]["identifier"][0]["value"] == "KHP01"


def test_service_label_is_text_not_a_code_and_warned():
    b, w = load("278_req_001.x12")
    pos = res(b, "Claim")[0]["item"][0]["productOrService"]
    assert pos.get("text") == "lumbar-mri" and "coding" not in pos
    assert len(w) >= 2


def test_full_urls_are_deterministic():
    a, _ = load("278_req_001.x12")
    b, _ = load("278_req_001.x12")
    assert [e["fullUrl"] for e in a["entry"]] == [e["fullUrl"] for e in b["entry"]]


@pytest.mark.parametrize("name,word", [
    ("278_req_003_missing_hi.x12", "HI"),
    ("278_req_004_missing_subscriber.x12", "IL"),
    ("278_req_005_bad_date.x12", "date"),
])
def test_bad_input_raises_x12error(name, word):
    with pytest.raises(X12Error) as ei:
        load(name)
    assert word.lower() in str(ei.value).lower()
