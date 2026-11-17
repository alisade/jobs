from assistant.request_builder import build_request, prefix_hash
from conftest import NOW


def test_request_has_tools_system_and_the_question():
    req = build_request("is the ridgeline tent in stock?", now=NOW, store_id="012")
    assert {t["name"] for t in req["tools"]} == {"search_products", "check_inventory", "get_order_status",
                                                 "start_return", "store_hours"}
    assert req["messages"][-1]["role"] == "user"
    assert "ridgeline" in req["messages"][-1]["content"]


def test_prefix_is_stable_within_one_process():
    a = build_request("first question", now=NOW)
    b = build_request("second question", now=NOW)
    assert prefix_hash(a) == prefix_hash(b)
