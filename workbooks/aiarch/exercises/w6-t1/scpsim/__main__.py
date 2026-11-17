"""CLI: python -m scpsim <requests.json> [--layout org/layout.json] [--attachments policies/attachments.json]

Prints one line per request: expected (if given), decision, and the deny statements that matched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import evaluate, load_org


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("requests")
    ap.add_argument("--layout", default="org/layout.json")
    ap.add_argument("--attachments", default="policies/attachments.json")
    ap.add_argument("--policies", default="policies")
    a = ap.parse_args()
    org = load_org(a.layout, a.attachments, a.policies)
    reqs = json.loads(Path(a.requests).read_text())
    bad = 0
    for r in reqs:
        d = evaluate(org, r)
        got = "ALLOW" if d.allowed else "DENY"
        exp = r.get("expect")
        flag = "" if exp is None else ("ok  " if exp == got else "MISMATCH")
        if exp is not None and exp != got:
            bad += 1
        print(f"{flag:8} {got:5} {r.get('name', r['action'])}  {' '.join(d.denied_by) or d.reason}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
