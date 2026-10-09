"""Hidden checks for ms/w7-t1 (flow definition behaviour)."""
from flowsim.engine import iso_seconds, retry_delays, run_flow, validate_graph
from flowsim.scenario import outcome

STARTER_ACTIONS = {"List_PO_lines", "Compose_payload", "Send_to_Contoso_Parts", "Mark_PO_as_sent"}
TRIGGER_CONDITION = "@equals(triggerOutputs()?['body/statuscode'], 100000003)"


def _send(definition):
    return definition["actions"]["Try"]["actions"]["Send_to_Contoso_Parts"]


def _walk(actions):
    for name, a in actions.items():
        yield name, a
        if a.get("type") == "Scope":
            yield from _walk(a.get("actions", {}))


def test_retry_policy_retries_429(definition):
    policy = _send(definition)["inputs"].get("retryPolicy")
    if policy is not None:
        assert policy.get("type", "").lower() in ("default", "fixed", "exponential"), \
            "retry policy must retry (type default, fixed or exponential)"
    delays = retry_delays(policy)
    assert len(delays) >= 3, "allow at least 3 retries"
    assert sum(delays) >= 60, "retries should span at least the 60 s APIM rate-limit window"


def test_retry_policy_shape_valid(definition):
    policy = _send(definition)["inputs"].get("retryPolicy")
    if policy and policy.get("type", "").lower() in ("fixed", "exponential"):
        assert 1 <= int(policy["count"]) <= 90
        assert 5 <= iso_seconds(policy["interval"]) <= 86400
        for k in ("minimumInterval", "maximumInterval"):
            if k in policy:
                iso_seconds(policy[k])


def test_catch_runs_after_failed_and_timedout(definition):
    ra = definition["actions"]["Catch"].get("runAfter", {})
    assert set(ra.get("Try", [])) >= {"Failed", "TimedOut"}


def test_catch_ends_run_failed(definition):
    catch = definition["actions"]["Catch"]["actions"]
    terms = [a for _, a in _walk(catch) if a.get("type") == "Terminate"]
    top_terms = [a for n, a in definition["actions"].items()
                 if a.get("type") == "Terminate" and "Catch" in (a.get("runAfter") or {})]
    allt = terms + top_terms
    assert allt, "the catch path must end with Terminate"
    assert all(t["inputs"].get("runStatus") == "Failed" for t in allt)
    assert all((t["inputs"].get("runError") or {}).get("message") for t in allt), "give Terminate a runError message"


def test_catch_captures_failure_details(definition):
    catch = definition["actions"]["Catch"]["actions"]
    blob = str(catch)
    assert "result('Try')" in blob, "use result('Try') to capture what failed"
    connectors = [a for _, a in _walk(catch) if a.get("type") in ("OpenApiConnection", "ApiConnection", "Http")]
    assert connectors, "notify someone or flag the PO from the catch path"


def test_no_action_lost_and_order_kept(definition):
    try_actions = definition["actions"]["Try"]["actions"]
    assert STARTER_ACTIONS <= set(try_actions)
    assert try_actions["Mark_PO_as_sent"]["runAfter"] == {"Send_to_Contoso_Parts": ["Succeeded"]}
    assert _send(definition)["type"] == "OpenApiConnection"
    assert _send(definition)["inputs"]["host"]["operationId"] == "SubmitPurchaseOrder"


def test_graph_valid(definition):
    assert validate_graph(definition["actions"]) == []


def test_trigger_condition_unchanged(definition):
    t = definition["triggers"]["When_a_PO_is_approved"]
    assert t.get("conditions") == [{"expression": TRIGGER_CONDITION}], \
        "the trigger condition is correct (only Approved POs); do not change it"


def test_replay_delivers_everything(definition):
    o = outcome(definition)
    assert o["silently_lost"] == 0, f"POs still lost silently: {o}"
    assert o["delivered"] >= 0.95 * o["total"], f"too few POs delivered: {o}"


def test_permanent_429_fails_the_run_loudly(definition):
    def always_429(name, inputs, clock, body):
        if inputs.get("host", {}).get("operationId") == "SubmitPurchaseOrder":
            return 429, {"Retry-After": "30"}, {"message": "Rate limit is exceeded."}
        return 200, {}, {}
    run = run_flow(definition, always_429, 0.0, {"contoso_ponumber": "PO-X"})
    assert run.status == "Failed", "a PO that could not be sent must leave a Failed run"


def test_hard_400_not_hidden(definition):
    def bad_request(name, inputs, clock, body):
        if inputs.get("host", {}).get("operationId") == "SubmitPurchaseOrder":
            return 400, {}, {"message": "supplierCode is not valid"}
        return 200, {}, {}
    run = run_flow(definition, bad_request, 0.0, {"contoso_ponumber": "PO-Y"})
    assert run.status == "Failed"
    sends = [r for r in run.records if r.name == "Send_to_Contoso_Parts"]
    assert len(sends[0].attempts) == 1, "4xx other than 408/429 must not be retried"


def test_answer_names_root_cause():
    import pathlib
    text = (pathlib.Path(__file__).resolve().parent.parent.parent / "ANSWER.md").read_text().lower()
    assert "retry" in text and "429" in text and ("terminate" in text or "succeeded" in text)
