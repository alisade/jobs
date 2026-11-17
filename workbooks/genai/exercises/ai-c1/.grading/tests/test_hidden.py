"""Hidden checks for genai/ai-c1."""

from conftest import make, payload, session_run


def _call(srv, name, args):
    return session_run(srv, lambda s: s.call_tool(name, args))


def _tools(srv):
    return {t.name: t for t in session_run(srv, lambda s: s.list_tools()).tools}


def test_read_only_by_default():
    assert set(_tools(make()[0])) == {"find_product", "store_stock", "order_lookup"}


def test_write_tools_only_with_scope():
    assert set(_tools(make(write_scope=True)[0])) == {"find_product", "store_stock", "order_lookup",
                                                       "prepare_hold", "hold_item_for_customer"}


def test_descriptions_are_written_for_a_model():
    for t in _tools(make(write_scope=True)[0]).values():
        assert t.description and len(t.description) >= 40, t.name
        assert "GET /" not in t.description and "POST /" not in t.description


def test_find_product_schema_caps_limit():
    t = _tools(make()[0])["find_product"]
    lim = t.inputSchema["properties"]["limit"]
    assert lim.get("maximum") == 10 and lim.get("minimum") == 1
    assert _call(make()[0], "find_product", {"query": "tent", "limit": 50}).isError is True


def test_find_product_is_compact_and_hints_more():
    r = _call(make()[0], "find_product", {"query": "tent", "limit": 3})
    body = payload(r)
    assert len(body["results"]) == 3
    assert body["more_results"] is True and "hint" in body
    for item in body["results"]:
        assert "description" not in item and "supplier_cost_cents" not in item
        assert {"sku", "name"} <= set(item)
    few = payload(_call(make()[0], "find_product", {"query": "lantern"}))
    assert few["more_results"] is False


def test_store_stock_defaults_to_own_store_and_explains_unknown_sku():
    srv = make()[0]
    assert payload(_call(srv, "store_stock", {"sku": "KO-TENT-2P"}))["available"] == 3
    assert payload(_call(srv, "store_stock", {"sku": "KO-TENT-2P", "store_id": "087"}))["available"] == 0
    bad = _call(srv, "store_stock", {"sku": "KO-NOPE"})
    assert bad.isError is True and "find_product" in bad.content[0].text


def test_order_lookup_scoped_to_store_and_minimized():
    srv = make()[0]
    own = _call(srv, "order_lookup", {"order_id": "K-5501"})
    assert own.isError is False
    text = own.content[0].text
    assert "ready_for_pickup" in text and "Maya" in text
    assert "maya.o@example.com" not in text and "555-0100" not in text and "Okafor" not in text
    other = _call(srv, "order_lookup", {"order_id": "K-5502"})
    missing = _call(srv, "order_lookup", {"order_id": "K-9999"})
    assert other.isError is True and missing.isError is True
    assert "Lee" not in other.content[0].text
    assert other.content[0].text.replace("K-5502", "X") == missing.content[0].text.replace("K-9999", "X")


def test_hold_needs_prepare_then_confirm_once():
    srv, backend, _ = make(write_scope=True)

    async def flow(s):
        p = await s.call_tool("prepare_hold", {"sku": "KO-LAMP-1", "customer_name": "Maya", "quantity": 2})
        assert p.isError is False
        tok = payload(p)["confirmation_token"]
        assert backend.holds == []
        ok = await s.call_tool("hold_item_for_customer", {"confirmation_token": tok})
        again = await s.call_tool("hold_item_for_customer", {"confirmation_token": tok})
        fake = await s.call_tool("hold_item_for_customer", {"confirmation_token": "hold_made_up_token"})
        return ok, again, fake

    ok, again, fake = session_run(srv, flow)
    assert ok.isError is False and payload(ok)["hold_id"]
    assert again.isError is True and fake.isError is True
    assert len(backend.holds) == 1 and backend.available("KO-LAMP-1", "012") == 7


def test_hold_token_expires():
    srv, backend, clock = make(write_scope=True)

    async def flow(s):
        p = await s.call_tool("prepare_hold", {"sku": "KO-LAMP-1", "customer_name": "Maya"})
        clock.t += 121
        return await s.call_tool("hold_item_for_customer", {"confirmation_token": payload(p)["confirmation_token"]})

    r = session_run(srv, flow)
    assert r.isError is True and backend.holds == []


def test_prepare_checks_stock():
    srv, backend, _ = make(write_scope=True)
    r = _call(srv, "prepare_hold", {"sku": "KO-COOL-45", "customer_name": "Lee", "quantity": 3})
    assert r.isError is True and "1" in r.content[0].text


def test_hours_resource():
    srv = make()[0]

    async def flow(s):
        tpl = await s.list_resource_templates()
        uris = [t.uriTemplate for t in tpl.resourceTemplates]
        rr = await s.read_resource("kestrel://stores/012/hours")
        return uris, rr.contents[0].text

    uris, text = session_run(srv, flow)
    assert "kestrel://stores/{store_id}/hours" in uris
    assert "Mon-Sat" in text


def test_audit_records_successes_and_failures():
    srv = make()[0]
    _call(srv, "find_product", {"query": "tent"})
    _call(srv, "order_lookup", {"order_id": "K-5502"})
    entries = [(e["tool"], e["ok"]) for e in srv.audit]
    assert ("find_product", True) in entries
    assert ("order_lookup", False) in entries
