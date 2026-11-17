from mcputil import call, session, tools


def test_four_tools_and_no_identity_arguments():
    srv, _ = session()
    ts = {t.name: t for t in tools(srv)}
    assert set(ts) == {"create_change", "get_change", "list_my_open_changes", "add_comment"}
    for t in ts.values():
        props = set((t.input_schema or {}).get("properties", {}))
        assert not props & {"requester", "user", "author", "caller"}, f"{t.name} lets the model choose identity: {props}"


def test_create_change_for_signed_in_user():
    srv, store = session("mchen")
    err, body = call(srv, "create_change", {"service": "agent-gateway", "summary": "Raise gateway rate limit to 50 rps",
                                             "risk": "low", "window_start": "2026-11-20T02:00:00Z"})
    assert not err, body
    assert store.changes[body["change_id"]]["requester"] == "mchen"


def test_unknown_service_gets_actionable_error():
    srv, _ = session()
    err, body = call(srv, "create_change", {"service": "claims-intak", "summary": "Rotate TLS certificate again",
                                             "risk": "low", "window_start": "2026-11-20T02:00:00Z"})
    assert err and "claims-intake" in str(body)
