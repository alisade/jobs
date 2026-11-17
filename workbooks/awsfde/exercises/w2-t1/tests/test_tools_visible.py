"""Visible checks for w2-t1. The grader runs more."""

from __future__ import annotations

from w2t1_support import ctx

from order_tools.handler import lambda_handler


def test_search_still_works():
    out = lambda_handler({"query": "Denver"}, ctx("tw_orders___search"))
    assert out["results"][0]["order_id"] == "PO-48812"


def test_lookup_order_through_gateway_name():
    out = lambda_handler({"order_id": "PO-48812"}, ctx("tw_orders___lookup_order"))
    assert out["status"] == "SHIPPED"
