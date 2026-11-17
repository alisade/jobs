"""The three tool implementations. Each takes the Gateway event (the tool arguments) and returns a
JSON-serializable result."""

from __future__ import annotations

import json
import pathlib

DATA = json.loads((pathlib.Path(__file__).resolve().parent / "orders.json").read_text())


class NotFound(Exception):
    pass


def _order(order_id: str) -> dict:
    for o in DATA["orders"]:
        if o["order_id"] == order_id:
            return o
    raise NotFound(f"No purchase order {order_id}.")


def search(args: dict) -> dict:
    q = str(args["query"]).lower()
    hits = [o for o in DATA["orders"]
            if q in o["customer"].lower() or q in o["status"].lower() or any(q in ln["sku"].lower() for ln in o["lines"])]
    return {"results": [{"order_id": o["order_id"], "customer": o["customer"], "status": o["status"]} for o in hits[:5]]}


def lookup_order(args: dict) -> dict:
    o = _order(args["order_id"])
    return {k: o[k] for k in ("order_id", "customer", "status", "shipment_id", "placed", "lines")}


def get_invoice_total(args: dict) -> dict:
    o = _order(args["order_id"])
    subtotal = round(sum(ln["qty"] * ln["unit_price"] for ln in o["lines"]), 2)
    tax = round(subtotal * DATA["tax_rate"], 2)
    return {"order_id": o["order_id"], "currency": "USD", "subtotal": subtotal, "tax": tax,
            "total": round(subtotal + tax, 2)}


HANDLERS = {"search": search, "lookup_order": lookup_order, "get_invoice_total": get_invoice_total}
