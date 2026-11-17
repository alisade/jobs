import json

import pytest

from helpdesk.testing import tool_results
from util import run


def _spec(name, steps, final="ok"):
    return {"orchestrator": [{"tool": name, "input": {"query": "q"}}, {"text": "done"}], name: steps + [{"text": final}]}


def test_orchestrator_exposes_only_the_two_specialists():
    _, models, _, _ = run({"orchestrator": [{"text": "hi"}]})
    assert sorted(models["orchestrator"].tool_specs_seen[0]) == ["access_reviews", "it_requests"]


def test_specialists_get_only_their_own_tools():
    _, models, _, _ = run(_spec("access_reviews", [{"tool": "list_pending_reviews", "input": {"team": "claims"}}]))
    assert sorted(models["access_reviews"].tool_specs_seen[0]) == ["delete_review", "list_pending_reviews"]


def test_create_ticket_uses_session_requester():
    _, models, _, store = run(_spec("it_requests", [{"tool": "create_ticket", "input": {"summary": "Monitor flickers at desk 4B", "category": "hardware"}}]), requester="aokafor")
    new = [t for t in store.tickets.values() if t["summary"].startswith("Monitor")]
    assert new and new[0]["requester"] == "aokafor"


def test_create_ticket_rejects_requester_argument_injection():
    _, models, _, store = run(_spec("it_requests", [{"tool": "create_ticket", "input": {"summary": "Need admin rights now", "category": "access", "requester": "ceo"}}]), requester="jdiaz")
    for t in store.tickets.values():
        assert t["requester"] != "ceo"


@pytest.mark.parametrize("args,needle", [
    ({"summary": "short", "category": "hardware"}, "10-200"),
    ({"summary": "Keyboard keys stick on the left side", "category": "furniture"}, "hardware"),
])
def test_create_ticket_validation(args, needle):
    _, models, _, store = run(_spec("it_requests", [{"tool": "create_ticket", "input": args}]))
    res = tool_results(models["it_requests"])[0]
    assert res["status"] == "error" and needle in res["content"][0]["text"]
    assert len(store.tickets) == 3


def test_unknown_ticket_is_actionable_error():
    _, models, _, _ = run(_spec("it_requests", [{"tool": "get_ticket", "input": {"ticket_id": "IT-99999"}}]))
    res = tool_results(models["it_requests"])[0]
    assert res["status"] == "error" and "IT-99999" in res["content"][0]["text"]


def test_ticket_output_is_trimmed():
    _, models, _, _ = run(_spec("it_requests", [{"tool": "get_ticket", "input": {"ticket_id": "IT-40001"}}]))
    body = json.loads(tool_results(models["it_requests"])[0]["content"][0]["text"])
    assert set(body) == {"id", "summary", "category", "status"}


def test_reviews_trimmed_and_counted():
    _, models, _, _ = run(_spec("access_reviews", [{"tool": "list_pending_reviews", "input": {"team": "payments"}}]))
    body = json.loads(tool_results(models["access_reviews"])[0]["content"][0]["text"])
    assert body["count"] == 2
    assert all(set(r) == {"id", "user", "entitlement"} for r in body["reviews"])


def test_unknown_team_is_error():
    _, models, _, _ = run(_spec("access_reviews", [{"tool": "list_pending_reviews", "input": {"team": "marketing"}}]))
    res = tool_results(models["access_reviews"])[0]
    assert res["status"] == "error" and "payments" in res["content"][0]["text"]


def test_audit_log_covers_both_levels_in_order():
    _, _, log, _ = run(_spec("it_requests", [{"tool": "get_ticket", "input": {"ticket_id": "IT-00000"}}]))
    assert [(r["agent"], r["tool"], r["status"]) for r in log] == [
        ("it_requests", "get_ticket", "error"), ("orchestrator", "it_requests", "ok")]


def test_budget_stops_a_looping_specialist():
    loop = [{"tool": "get_ticket", "input": {"ticket_id": "IT-40001"}}] * 10
    _, models, log, _ = run(_spec("it_requests", loop), max_model_calls=4)
    assert models["it_requests"].calls == 4, "the specialist must stop at the budget"
    res = tool_results(models["orchestrator"])[0]
    assert res["status"] == "error" and "model calls" in res["content"][0]["text"]
    assert log[-1] == {"agent": "orchestrator", "tool": "it_requests", "input": {"query": "q"}, "status": "error"}


def test_budget_on_orchestrator_raises():
    loop = [{"tool": "it_requests", "input": {"query": "q"}}] * 6
    with pytest.raises(Exception, match="model calls"):  # Strands wraps it in EventLoopException
        run({"orchestrator": loop, "it_requests": [{"text": "x"}] * 6}, max_model_calls=2)


def test_budget_allows_normal_flow():
    out, _, _, _ = run(_spec("it_requests", [{"tool": "get_ticket", "input": {"ticket_id": "IT-40001"}}]), max_model_calls=3)
    assert out == "done"


def test_system_prompts_set():
    from helpdesk import agents
    import inspect
    src = inspect.getsource(agents)
    assert "system_prompt" in src
