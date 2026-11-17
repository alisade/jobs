from helpdesk.testing import tool_results
from util import run


def test_routes_to_it_specialist_and_reads_ticket():
    out, models, log, _ = run({
        "orchestrator": [{"tool": "it_requests", "input": {"query": "status of IT-40002"}}, {"text": "In progress."}],
        "it_requests": [{"tool": "get_ticket", "input": {"ticket_id": "IT-40002"}}, {"text": "IT-40002 is in progress"}],
    })
    assert out == "In progress."
    res = tool_results(models["it_requests"])[0]
    assert res["status"] == "success" and "in_progress" in res["content"][0]["text"]
    # the orchestrator saw the specialist's answer as the tool result
    assert "IT-40002 is in progress" in tool_results(models["orchestrator"])[0]["content"][0]["text"]


def test_delete_tools_are_blocked_and_audited():
    _, models, log, store = run({
        "orchestrator": [{"tool": "access_reviews", "input": {"query": "clean up AR-901"}}, {"text": "done"}],
        "access_reviews": [{"tool": "delete_review", "input": {"review_id": "AR-901"}}, {"text": "could not"}],
    })
    assert len(store.reviews) == 4, "the delete must not run"
    assert {"agent": "access_reviews", "tool": "delete_review", "input": {"review_id": "AR-901"}, "status": "blocked"} in log


def test_bad_ticket_id_gets_an_actionable_error():
    _, models, _, _ = run({
        "orchestrator": [{"tool": "it_requests", "input": {"query": "ticket 42"}}, {"text": "?"}],
        "it_requests": [{"tool": "get_ticket", "input": {"ticket_id": "42"}}, {"text": "bad id"}],
    })
    res = tool_results(models["it_requests"])[0]
    assert res["status"] == "error" and "IT-12345" in res["content"][0]["text"]
