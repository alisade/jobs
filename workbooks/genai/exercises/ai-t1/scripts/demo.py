"""Reproduce the incident: 10 worker processes (each with its own PYTHONHASHSEED, like the 4 gunicorn
workers x 12 pods in prod) each take the next request, round robin, as the load balancer does.
A simulated provider cache reports hits when the prefix bytes match an earlier request.
Prints per-worker prefix hashes, tool order, the cache hit ratio and the cost."""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from assistant.cost import cache_hit_ratio, cost_usd  # noqa: E402

QUESTIONS = ["is the ridgeline tent in stock?", "what headlamp for night hikes?", "where is my order K-1002?",
             "is store 012 open now?"]
seen: set[str] = set()
usages = []
for n, seed in enumerate(["101", "202", "303", "404", "505", "606", "707", "808", "909", "1001"]):
    env = dict(os.environ, PYTHONHASHSEED=seed)
    raw = subprocess.run([sys.executable, os.path.join(HERE, "worker.py"), QUESTIONS[n % len(QUESTIONS)]], env=env,
                         capture_output=True, text=True, timeout=60, check=True).stdout
    rows = json.loads(raw)
    print(f"worker seed={seed:>4} prefix={rows[0]['prefix_hash']} tools={','.join(rows[0]['tools'])}")
    for r in rows:
        hit = r["prefix_hash"] in seen
        seen.add(r["prefix_hash"])
        usages.append({"input_tokens": 60, "output_tokens": 180,
                       "cache_read_input_tokens": r["prefix_tokens"] if hit else 0,
                       "cache_creation_input_tokens": 0 if hit else r["prefix_tokens"]})
print(f"distinct prefixes: {len(seen)}  cache hit ratio: {cache_hit_ratio(usages):.0%}  "
      f"cost for {len(usages)} requests: ${sum(cost_usd(u) for u in usages):.4f}")
