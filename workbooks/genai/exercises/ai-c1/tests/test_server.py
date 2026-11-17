from conftest import make, payload, session_run


def test_lists_find_product():
    srv, _, _ = make()
    tools = session_run(srv, lambda s: s.list_tools())
    assert "find_product" in {t.name for t in tools.tools}


def test_find_product_returns_matches():
    srv, _, _ = make()
    r = session_run(srv, lambda s: s.call_tool("find_product", {"query": "ridgeline"}))
    assert r.isError is False
    assert "KO-TENT-2P" in r.content[0].text
