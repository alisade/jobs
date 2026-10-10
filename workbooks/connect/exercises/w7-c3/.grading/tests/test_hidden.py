"""Hidden tests for connect/w7-c3 (copied to tests_hidden/ by the grader)."""
import base64
import hashlib
import json
from collections import defaultdict

import pytest
from helpers import decoded_rows, duck, firehose_event, load_module, sample_ctrs

CTRS = sample_ctrs()
REQUIRED = {
    "contact_id", "initial_contact_id", "channel", "initiation_method", "initiation_ts", "disconnect_ts", "dt",
    "duration_seconds", "queue_name", "queue_seconds", "agent_username", "answered", "abandoned", "contained",
    "talk_seconds", "hold_seconds", "acw_seconds", "handle_seconds", "disconnect_reason", "lex_intent",
    "caller_verified", "phone_hash", "phone_last4", "recorded", "retention_class", "attributes",
}


@pytest.fixture(scope="module")
def run():
    t = load_module()
    out = t.lambda_handler(firehose_event(CTRS, raw=[b"not json at all", b"{}"]), None)
    return out


@pytest.fixture(scope="module")
def rows(run):
    return decoded_rows(run)


def by_id(rows):
    return {r["contact_id"]: r for r in rows}


def test_synthetic_canary_contacts_are_dropped(run):
    synth = [i for i, c in enumerate(CTRS) if c["Attributes"].get("synthetic") == "true"]
    assert synth
    for i in synth:
        assert run["records"][i]["result"] == "Dropped"


def test_undecodable_and_non_ctr_records_fail_without_crashing_the_batch(run):
    raw = run["records"][-2:]
    assert [r["result"] for r in raw] == ["ProcessingFailed", "ProcessingFailed"]
    assert base64.b64decode(raw[0]["data"]) == b"not json at all"
    assert len(run["records"]) == len(CTRS) + 2


def test_partition_keys_for_dynamic_partitioning(run):
    ok = [(c, r) for c, r in zip(CTRS, run["records"]) if r["result"] == "Ok"]
    for c, r in ok:
        keys = r["metadata"]["partitionKeys"]
        assert keys["channel"] == c["Channel"].lower()
        assert keys["dt"] == c["InitiationTimestamp"][:10]
        assert keys["retention"] in ("legal-hold", "recorded-7y", "standard-3y")


def test_output_rows_have_the_documented_columns(rows):
    for r in rows:
        assert REQUIRED <= set(r), REQUIRED - set(r)


def test_no_raw_phone_numbers_anywhere(run):
    numbers = {c["CustomerEndpoint"]["Address"] for c in CTRS if c.get("CustomerEndpoint")}
    blob = "".join(base64.b64decode(r["data"]).decode() for r in run["records"] if r["result"] == "Ok")
    assert not [n for n in numbers if n in blob]


def test_phone_hash_is_salted_sha256_and_last4_kept(monkeypatch):
    monkeypatch.setenv("PHONE_HASH_SALT", "pepper-2026")
    t = load_module()
    c = next(c for c in CTRS if c.get("CustomerEndpoint"))
    row = decoded_rows(t.lambda_handler(firehose_event([c]), None))[0]
    num = c["CustomerEndpoint"]["Address"]
    assert row["phone_hash"] == hashlib.sha256(("pepper-2026" + num).encode()).hexdigest()
    assert row["phone_last4"] == num[-4:]


def test_deny_listed_attributes_are_removed(rows):
    for r in rows:
        assert not {k.lower() for k in r["attributes"]} & {"cardnumber", "ssn", "dob", "cvv", "pin", "password"}


def test_ssn_and_luhn_valid_card_numbers_in_free_text_are_redacted():
    t = load_module()
    c = json.loads(json.dumps(CTRS[0]))
    c["Attributes"] = {"notes": "SSN 123-45-6789, card 4111-1111-1111-1111, order 1234 5678 9012 3456", "selfServiceOutcome": "x"}
    row = decoded_rows(t.lambda_handler(firehose_event([c]), None))[0]
    notes = row["attributes"]["notes"]
    assert "123-45-6789" not in notes and "4111-1111-1111-1111" not in notes
    assert "1234 5678 9012 3456" in notes  # not Luhn-valid: an order number, keep it
    assert "[REDACTED]" in notes


def test_retention_classes(rows):
    ids = by_id(rows)
    for c in CTRS:
        if c["Attributes"].get("synthetic") == "true":
            continue
        want = "legal-hold" if c["Attributes"].get("legalHold") == "true" else ("recorded-7y" if c.get("Recording") else "standard-3y")
        assert ids[c["ContactId"]]["retention_class"] == want


def test_handle_time_is_talk_plus_hold_plus_acw(rows):
    ids = by_id(rows)
    for c in CTRS:
        r = ids.get(c["ContactId"])
        if not r:
            continue
        a = c.get("Agent")
        if a:
            assert r["handle_seconds"] == a["AgentInteractionDuration"] + a["CustomerHoldDuration"] + a["AfterContactWorkDuration"]
        else:
            assert r["handle_seconds"] is None


def test_answered_abandoned_contained_flags(rows):
    ids = by_id(rows)
    for c in CTRS:
        r = ids.get(c["ContactId"])
        if not r:
            continue
        assert r["answered"] == bool(c.get("Agent"))
        assert r["abandoned"] == (bool(c.get("Queue")) and not c.get("Agent"))
        assert r["contained"] == (not c.get("Queue") and not c.get("Agent") and c["Attributes"].get("selfServiceOutcome") == "resolved")


def test_duration_seconds(rows):
    r = rows[0]
    from datetime import datetime

    f = "%Y-%m-%dT%H:%M:%SZ"
    assert r["duration_seconds"] == int((datetime.strptime(r["disconnect_ts"], f) - datetime.strptime(r["initiation_ts"], f)).total_seconds())


def expected_queue_daily():
    agg = defaultdict(lambda: {"offered": 0, "answered": 0, "abandoned": 0, "short": 0, "within": 0, "handle": []})
    for c in CTRS:
        if c["Attributes"].get("synthetic") == "true" or not c.get("Queue"):
            continue
        k = (c["InitiationTimestamp"][:10], c["Queue"]["Name"])
        a = agg[k]
        a["offered"] += 1
        if c.get("Agent"):
            a["answered"] += 1
            if c["Queue"]["Duration"] <= 60:
                a["within"] += 1
            g = c["Agent"]
            a["handle"].append(g["AgentInteractionDuration"] + g["CustomerHoldDuration"] + g["AfterContactWorkDuration"])
        else:
            a["abandoned"] += 1
            if c["Queue"]["Duration"] < 5:
                a["short"] += 1
    return agg


def test_queue_daily_service_level_excludes_short_abandons(rows):
    con = duck(rows)
    got = {(d, q): sl for d, q, sl in con.execute("SELECT dt, queue_name, service_level_60s FROM queue_daily").fetchall()}
    exp = expected_queue_daily()
    assert set(got) == set(exp)
    for k, a in exp.items():
        assert got[k] == pytest.approx(a["within"] / (a["offered"] - a["short"]), abs=1e-3)


def test_queue_daily_abandon_rate_and_aht(rows):
    con = duck(rows)
    got = {(d, q): (ar, aht) for d, q, ar, aht in con.execute("SELECT dt, queue_name, abandon_rate, avg_handle_seconds FROM queue_daily").fetchall()}
    for k, a in expected_queue_daily().items():
        assert got[k][0] == pytest.approx(a["abandoned"] / a["offered"], abs=1e-3)
        if a["handle"]:
            assert got[k][1] == pytest.approx(sum(a["handle"]) / len(a["handle"]), abs=0.1)


def test_agent_occupancy(rows):
    import csv
    from helpers import ROOT

    con = duck(rows)
    got = {(d, a): o for d, a, o in con.execute("SELECT dt, agent_username, occupancy FROM agent_occupancy").fetchall()}
    handle = defaultdict(int)
    for c in CTRS:
        g = c.get("Agent")
        if g and c["Attributes"].get("synthetic") != "true":
            handle[(c["InitiationTimestamp"][:10], g["Username"])] += g["AgentInteractionDuration"] + g["CustomerHoldDuration"] + g["AfterContactWorkDuration"]
    with open(ROOT / "data" / "agent_staffing.csv") as f:
        staffing = list(csv.DictReader(f))
    assert len(got) == len(staffing)  # agents with zero contacts still appear
    for s in staffing:
        k = (s["dt"], s["agent_username"])
        assert got[k] == pytest.approx(handle[k] / int(s["staffed_seconds"]), abs=1e-3)


def test_containment_by_intent(rows):
    con = duck(rows)
    got = {i: (n, k) for i, n, k in con.execute("SELECT lex_intent, contacts, contained FROM containment_by_intent").fetchall()}
    exp = defaultdict(lambda: [0, 0])
    for c in CTRS:
        if c["Attributes"].get("synthetic") == "true":
            continue
        i = c["Attributes"].get("lexIntent") or "none"
        exp[i][0] += 1
        if not c.get("Queue") and not c.get("Agent") and c["Attributes"].get("selfServiceOutcome") == "resolved":
            exp[i][1] += 1
    assert got == {k: tuple(v) for k, v in exp.items()}
