"""Synthetic check: what the Managed Agents platform does on every session. Fetch a fresh
access token from the IdP, call the gateway, tally the results.

    python scripts/probe.py [--n 40]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys

import httpx
import jwt

IDP = "http://127.0.0.1:18210"
GATEWAY = "http://127.0.0.1:18211"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    args = ap.parse_args()
    tally: collections.Counter[tuple[str, int]] = collections.Counter()
    statuses: collections.Counter[int] = collections.Counter()
    with httpx.Client(timeout=5.0) as http:
        for i in range(args.n):
            try:
                tok = http.post(f"{IDP}/oauth/token", data={"client_id": "managed-agents"})
                tok.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"IdP unreachable: {exc} (run make setup)")
                return 2
            access = tok.json()["access_token"]
            kid = jwt.get_unverified_header(access).get("kid", "?")
            try:
                r = http.post(
                    f"{GATEWAY}/mcp",
                    headers={"authorization": f"Bearer {access}",
                             "accept": "application/json, text/event-stream"},
                    content=json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/list"}),
                )
            except httpx.HTTPError as exc:
                print(f"gateway unreachable: {exc} (run make setup)")
                return 2
            statuses[r.status_code] += 1
            tally[(kid, r.status_code)] += 1
    total = sum(statuses.values())
    bad = statuses.get(401, 0)
    print(f"{total} sessions: " + ", ".join(f"{c}x HTTP {s}" for s, c in sorted(statuses.items())))
    print(f"401 rate: {100 * bad / total:.0f}%")
    for (kid, status), count in sorted(tally.items()):
        print(f"  kid={kid:<10} HTTP {status}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
