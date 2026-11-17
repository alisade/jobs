"""One assistant worker process: builds requests and prints the cache prefix hash and tool order."""

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.request_builder import build_request, prefix_bytes, prefix_hash  # noqa: E402

questions = sys.argv[1:] or ["is the ridgeline tent in stock?"]
out = []
for i, q in enumerate(questions):
    now = dt.datetime(2026, 11, 12, 9, 0, i, tzinfo=dt.timezone.utc)
    req = build_request(q, now=now, store_id="012")
    out.append({"prefix_hash": prefix_hash(req), "prefix_tokens": len(prefix_bytes(req)) // 4,
                "tools": [t["name"] for t in req["tools"]]})
print(json.dumps(out))
