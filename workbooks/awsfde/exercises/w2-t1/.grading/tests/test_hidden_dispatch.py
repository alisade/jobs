"""Hidden checks for w2-t1: dispatch on the Gateway's <target>___<tool> name, error results the
agent can act on, a clean replay, and guards."""

from __future__ import annotations

import pytest
from w2t1_hidden_support import ROOT, ctx

from order_tools import tools
from order_tools.handler import lambda_handler, tool_name_from_context


@pytest.mark.parametrize("full,tool", [
    ("tw_orders___lookup_order", "lookup_order"),
    ("tw_orders___get_invoice_total", "get_invoice_total"),
    ("orders___search", "search"),
    ("acme-foods_orders_v2___lookup_order", "lookup_order"),
    ("x___get_invoice_total", "get_invoice_total"),
])
def test_tool_name_split_on_delimiter(full, tool):
    assert tool_name_from_context(ctx(full)) == tool


def test_unprefixed_name_is_used_as_is():
    assert tool_name_from_context(ctx("lookup_order")) == "lookup_order"


def test_invoice_total_dispatch():
    out = lambda_handler({"order_id": "PO-48812"}, ctx("tw_orders___get_invoice_total"))
    assert out["total"] == 941.76 and out["currency"] == "USD"


def test_target_with_underscores_dispatch():
    out = lambda_handler({"order_id": "PO-48830"}, ctx("acme_foods_orders___lookup_order"))
    assert out["order_id"] == "PO-48830"


def test_unknown_tool_is_an_error_result_not_an_exception():
    out = lambda_handler({}, ctx("tw_orders___delete_order"))
    assert isinstance(out, dict) and "error" in out
    assert out["error"]["code"] == "UNKNOWN_TOOL"
    assert "delete_order" in out["error"]["message"]


def test_missing_argument_is_an_error_result():
    out = lambda_handler({}, ctx("tw_orders___lookup_order"))
    assert isinstance(out, dict) and out.get("error", {}).get("code") == "INVALID_INPUT"


def test_not_found_still_reported():
    out = lambda_handler({"order_id": "PO-99999"}, ctx("tw_orders___lookup_order"))
    assert out["error"]["code"] == "NOT_FOUND"


def test_replay_has_no_function_errors():
    from replay.simulate import run
    r = run(ROOT)
    errors = [x for x in r["results"] if x["result"]["isError"]]
    # PO-99999 is the only legitimate miss in the recorded traffic
    assert len(errors) == 1 and errors[0]["args"] == {"order_id": "PO-99999"}, errors
    assert not any("[ERROR]" in ln for ln in r["lambda"])


def test_guard_tools_unchanged():
    assert tools.get_invoice_total({"order_id": "PO-48830"}) == {
        "order_id": "PO-48830", "currency": "USD", "subtotal": 1286.25, "tax": 102.9, "total": 1389.15}
    assert [o["order_id"] for o in tools.search({"query": "PAL-STD-48"})["results"]] == ["PO-48812", "PO-48817"]
