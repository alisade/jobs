"""Authoring tool: regenerate fixtures/recorded_turns.jsonl (deterministic, seed 2026).

python .grading/gen_fixtures.py   (from the exercise folder)
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentloop.tools import call_key  # noqa: E402

rng = random.Random(2026)
PRODUCTS = [
    ("LH-2201", "Arden linen table lamp", 89.0, "table lamp"),
    ("LH-2214", "Pilot brass floor lamp", 149.0, "floor lamp"),
    ("LH-3105", "Mesa wool area rug 5x8", 329.0, "wool rug"),
    ("LH-3120", "Dune jute runner 2x8", 79.0, "jute runner"),
    ("LH-4410", "Harbor oak side table", 199.0, "side table"),
    ("LH-4432", "Cove velvet accent chair", 449.0, "accent chair"),
    ("LH-5108", "Linden cotton duvet set queen", 139.0, "duvet set"),
    ("LH-5150", "Fern blackout curtains 84in", 64.0, "blackout curtains"),
    ("LH-6002", "Atlas ceramic planter large", 58.0, "ceramic planter"),
    ("LH-6040", "Ridge walnut wall shelf", 72.0, "wall shelf"),
]
uid = 0


def tid() -> str:
    global uid
    uid += 1
    return f"toolu_01{uid:010d}"


def tool_use(name: str, **inp) -> dict:
    return {"type": "tool_use", "id": tid(), "name": name, "input": inp}


def text(t: str) -> dict:
    return {"type": "text", "text": t}


def search_out(q: str, prods) -> str:
    rows = [{"sku": s, "title": t, "price": p} for s, t, p, _ in prods]
    return json.dumps({"query": q, "results": rows})


records = []
N = 140
FAIL_TURNS = {23, 61, 97, 118}  # parallel rounds where one upstream call fails
TIMEOUT_TURN = 97  # of those, the one that fails by being slow
RATE_LIMITED = {8, 23, 40, 77, 103, 131}
for i in range(N):
    sku, title, price, kind = PRODUCTS[i % len(PRODUCTS)]
    conv = f"conv-{rng.randrange(16**8):08x}"
    turn = f"turn-{i + 1:04d}"
    tools: dict[str, dict] = {}
    if i % 9 == 4 and i not in FAIL_TURNS:
        msg = f"What's your return window on a {kind}?"
        script = [{"content": [text("Lumen Home accepts returns within 30 days of delivery for unused items.")], "stop_reason": "end_turn"}]
    elif i % 7 == 2 and i not in FAIL_TURNS:
        oid = f"LH-ORD-{rng.randrange(10**6):06d}"
        msg = f"Where is my order {oid}?"
        u = tool_use("get_order", order_id=oid)
        tools[call_key("get_order", {"order_id": oid})] = {"output": json.dumps({"order_id": oid, "status": "shipped", "eta": "Oct 11"})}
        script = [
            {"content": [text("Let me look that up."), u], "stop_reason": "tool_use"},
            {"content": [text(f"Order {oid} has shipped and should arrive Oct 11.")], "stop_reason": "end_turn"},
        ]
    elif i % 3 == 0 or i in FAIL_TURNS:
        msg = f"Is the {title} in stock, and when could it get here?"
        s = tool_use("search_catalog", query=kind)
        tools[call_key("search_catalog", {"query": kind})] = {"output": search_out(kind, [(sku, title, price, kind)])}
        a, b = tool_use("check_stock", sku=sku), tool_use("shipping_estimate", sku=sku)
        if i in FAIL_TURNS and i == TIMEOUT_TURN:
            tools[call_key("check_stock", {"sku": sku})] = {"delay": 0.5, "output": "late"}
        elif i in FAIL_TURNS:
            tools[call_key("check_stock", {"sku": sku})] = {
                "error": "InventoryTimeout",
                "message": "inventory-svc.prod.lumen.internal:8443 read timed out after 1800 ms (pool inv-ro-3)",
            }
        else:
            tools[call_key("check_stock", {"sku": sku})] = {"output": json.dumps({"sku": sku, "store": 4, "online": 31})}
        tools[call_key("shipping_estimate", {"sku": sku})] = {"output": json.dumps({"sku": sku, "arrives": "Oct 13-15"})}
        final = (
            f"I could not check stock for the {title} just now, but it can arrive Oct 13-15."
            if i in FAIL_TURNS
            else f"The {title} is in stock (31 online) and can arrive Oct 13-15."
        )
        script = [
            {"content": [s], "stop_reason": "tool_use"},
            {"content": [text("Checking stock and delivery."), a, b], "stop_reason": "tool_use"},
            {"content": [text(final)], "stop_reason": "end_turn"},
        ]
    else:
        msg = f"Show me a {kind} under ${int(price) + 50}"
        s = tool_use("search_catalog", query=kind)
        tools[call_key("search_catalog", {"query": kind})] = {"output": search_out(kind, [(sku, title, price, kind)])}
        script = [
            {"content": [s], "stop_reason": "tool_use"},
            {"content": [text(f"The {title} at ${price:.0f} fits.")], "stop_reason": "end_turn"},
        ]
    final_text = script[-1]["content"][0]["text"]
    records.append(
        {
            "conversation_id": conv,
            "turn_id": turn,
            "history": [{"role": "user", "content": msg}],
            "script": script,
            "tools": tools,
            "rate_limit_calls": [1] if i in RATE_LIMITED and len(script) > 1 else ([0] if i in RATE_LIMITED else []),
            "final_text": final_text,
        }
    )

out = Path(__file__).resolve().parents[1] / "fixtures" / "recorded_turns.jsonl"
out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
print(f"wrote {len(records)} turns to {out}")
