import asyncio

D1 = {"decision": "deny", "reviewer": "md-007", "reason": "Criterion 2.b not met: no conservative therapy documented."}
D2 = {"decision": "approve", "reviewer": "rn-104", "reason": ""}


async def test_single_decision_lands_on_its_case(setup_cases):
    graph, svc, _ = setup_cases()
    out = await svc.submit_decision("PA-2026-0002", D1)
    assert out["determination"]["case_id"] == "PA-2026-0002"


async def test_two_reviewers_at_once(setup_cases):
    graph, svc, _ = setup_cases()
    a, b = await asyncio.gather(svc.submit_decision("PA-2026-0002", D1), svc.submit_decision("PA-2026-0003", D2))
    assert a["determination"]["case_id"] == "PA-2026-0002" and a["determination"]["decided_by"] == "md-007"
    assert b["determination"]["case_id"] == "PA-2026-0003" and b["determination"]["decided_by"] == "rn-104"
