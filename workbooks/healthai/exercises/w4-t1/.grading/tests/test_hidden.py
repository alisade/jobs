"""Hidden tests for healthai/w4-t1."""

import asyncio
import inspect
import json
from pathlib import Path

import pytest

import pa_graph.review_service as RS
from pa_graph.graph import config_for

EX = Path(__file__).resolve().parent.parent
DECIDE = {
    "PA-2026-0002": {"decision": "deny", "reviewer": "md-007", "reason": "Criterion 2.b not met: no conservative therapy documented."},
    "PA-2026-0003": {"decision": "approve", "reviewer": "rn-104", "reason": ""},
    "PA-2026-0005": {"decision": "approve", "reviewer": "rn-310", "reason": ""},
    "PA-2026-0006": {"decision": "pend", "reviewer": "rn-221", "reason": "Prior imaging report requested from the provider."},
    "PA-2026-0008": {"decision": "pend", "reviewer": "rn-221", "reason": "Requesting operative notes from the ordering surgeon."},
}
STATUS = {"approve": "approved", "deny": "denied", "pend": "pended"}


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
async def test_concurrent_burst_lands_every_decision_on_its_case(setup_cases, seed):
    graph, svc, cases = setup_cases(seed=seed)
    async with asyncio.timeout(10):
        res = await asyncio.gather(*(svc.submit_decision(c, d) for c, d in DECIDE.items()))
    for (cid, d), r in zip(DECIDE.items(), res):
        det = r["determination"]
        assert det["case_id"] == cid and det["decided_by"] == d["reviewer"] and det["status"] == STATUS[d["decision"]]
        assert r["member_id"] == cases[cid]["member_id"]


async def test_every_thread_finalized_exactly_once(setup_cases):
    graph, svc, _ = setup_cases(seed=9)
    await asyncio.gather(*(svc.submit_decision(c, d) for c, d in DECIDE.items()))
    for cid, d in DECIDE.items():
        st = graph.get_state(config_for(cid))
        assert st.next == ()
        fin = [a for a in st.values["audit"] if a["node"] == "finalize"]
        assert len(fin) == 1 and fin[0]["by"] == d["reviewer"]


async def test_audit_receipts_match_determinations(setup_cases):
    graph, svc, _ = setup_cases(seed=11)
    await asyncio.gather(*(svc.submit_decision(c, d) for c, d in DECIDE.items()))
    got = {(e["case_id"], e["decided_by"]) for e in svc.audit.events if e["event"] == "determination"}
    assert got == {(c, d["reviewer"]) for c, d in DECIDE.items()}


async def test_no_shared_mutable_config_left():
    shared = [n for n, v in vars(RS).items() if isinstance(v, dict) and "configurable" in v]
    assert not shared, f"module-level run config still present: {shared}"
    src = inspect.getsource(RS.ReviewService.submit_decision)
    assert "config_for(" in src


async def test_sequential_guard(setup_cases):
    graph, svc, _ = setup_cases(seed=3)
    for cid, d in DECIDE.items():
        r = await svc.submit_decision(cid, d)
        assert r["determination"]["case_id"] == cid


def test_findings():
    f = json.loads((EX / "findings.json").read_text())
    assert f["root_cause_file"].endswith("review_service.py")
    assert "RUN_CONFIG" in f["root_cause_symbol"] or "submit_decision" in f["root_cause_symbol"]
    assert f["thread_id_scheme_is_the_cause"] is False
    assert set(f["cases_with_wrong_determinations"]) >= {"PA-2026-0008"}
