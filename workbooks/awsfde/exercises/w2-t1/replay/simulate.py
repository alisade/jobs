"""Replay the Acme Foods pilot traffic after release 2026.11.12 through the emulated gateway.

    python -m replay.simulate --out run
"""

from __future__ import annotations

import argparse
import json
import logging
import pathlib

from .gateway import GATEWAY_ID, ROOT, TARGET_NAME, _Capture, call, load_handler, tools_list

# (time, session, user, method, tool, arguments) recorded from the agent's MCP client, 09:16-09:58
TRAFFIC = [
    ("09:16:41", "s-01", "dana@acme", "tools/list", None, None),
    ("09:16:44", "s-01", "dana@acme", "tools/call", "search", {"query": "Denver"}),
    ("09:16:49", "s-01", "dana@acme", "tools/call", "lookup_order", {"order_id": "PO-48812"}),
    ("09:17:02", "s-01", "dana@acme", "tools/call", "lookup_order", {"order_id": "PO-48812"}),
    ("09:21:10", "s-02", "raj@acme", "tools/list", None, None),
    ("09:21:15", "s-02", "raj@acme", "tools/call", "get_invoice_total", {"order_id": "PO-48830"}),
    ("09:21:31", "s-02", "raj@acme", "tools/call", "search", {"query": "OPEN"}),
    ("09:33:05", "s-03", "mei@acme", "tools/list", None, None),
    ("09:33:09", "s-03", "mei@acme", "tools/call", "search", {"query": "PAL-STD-48"}),
    ("09:33:14", "s-03", "mei@acme", "tools/call", "lookup_order", {"order_id": "PO-48817"}),
    ("09:33:20", "s-03", "mei@acme", "tools/call", "get_invoice_total", {"order_id": "PO-48817"}),
    ("09:41:52", "s-04", "dana@acme", "tools/list", None, None),
    ("09:41:58", "s-04", "dana@acme", "tools/call", "lookup_order", {"order_id": "PO-99999"}),
    ("09:42:07", "s-04", "dana@acme", "tools/call", "search", {"query": "Boise"}),
    ("09:57:30", "s-05", "raj@acme", "tools/list", None, None),
    ("09:57:36", "s-05", "raj@acme", "tools/call", "get_invoice_total", {"order_id": "PO-48812"}),
]


def run(root: pathlib.Path = ROOT) -> dict:
    handler = load_handler(root)
    cap = _Capture()
    lg = logging.getLogger("tidewater.order_tools")
    lg.addHandler(cap)
    gw_lines, results = [], []
    try:
        for i, (ts, sess, user, method, tool, args) in enumerate(TRAFFIC, start=1):
            mcp_id = f"{sess}-{i:03d}"
            if method == "tools/list":
                res = tools_list()
                gw_lines.append(json.dumps({"time": f"2026-11-12T{ts}Z", "gatewayId": GATEWAY_ID, "session": sess,
                                            "user": user, "method": method, "mcpMessageId": mcp_id,
                                            "tools": [t["name"] for t in res["tools"]], "status": "OK"}))
                continue
            full = f"{TARGET_NAME}___{tool}"
            res = call(handler, full, args, mcp_id)
            results.append({"tool": tool, "args": args, "result": res})
            gw_lines.append(json.dumps({"time": f"2026-11-12T{ts}Z", "gatewayId": GATEWAY_ID, "session": sess,
                                        "user": user, "method": method, "mcpMessageId": mcp_id, "name": full,
                                        "arguments": args, "isError": res["isError"],
                                        "result": res["content"][0]["text"][:200]}))
    finally:
        lg.removeHandler(cap)
    return {"gateway": gw_lines, "lambda": cap.lines, "results": results}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="run")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    r = run()
    (out / "gateway-2026-11-12.log").write_text("\n".join(r["gateway"]) + "\n")
    (out / "lambda-tw-order-tools-prod.log").write_text("\n".join(r["lambda"]) + "\n")
    errs = sum(1 for x in r["results"] if x["result"]["isError"])
    print(f"replayed {len(r['results'])} tool calls: {errs} returned isError; logs in {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
