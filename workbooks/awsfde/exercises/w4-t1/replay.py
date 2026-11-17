"""Replay sign-ins and API calls for every pilot user and write run/ (done).

Usage: python replay.py [outdir]
Reads config/*.json and data/users.json; the Lambda runs with config/lambda-env.json as environment.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import sys

from cognito_sim.pool import issue_tokens, jwt_authorizer, load, spa_token
from tenant_api import pretoken
from tenant_api.handler import handler

ROOT = pathlib.Path(__file__).resolve().parent


def main(out: str = "run") -> int:
    outdir = ROOT / out
    outdir.mkdir(exist_ok=True)
    for f in ("lambda.log", "authorizer.log", "requests.jsonl"):
        (outdir / f).unlink(missing_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s",
                        handlers=[logging.FileHandler(outdir / "lambda.log")], force=True)
    env = {k: v for k, v in load("lambda-env.json").items() if not k.startswith("_")}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    users = json.loads((ROOT / "data" / "users.json").read_text())
    rows, auth_lines = [], []
    try:
        for u in users:
            tokens = issue_tokens(u, pretoken.handler)
            tok = spa_token(tokens)
            event = jwt_authorizer(tok)
            claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
            auth_lines.append(json.dumps({"component": "jwt-authorizer", "sub": u["sub"], "token_use": tok["token_use"],
                                          "event_version": tokens["event_version"], "claims": sorted(claims)}))
            r = handler(event)
            body = json.loads(r["body"])
            rows.append({"user": u["username"], "provider": u["provider"], "expected_tenant": u["custom:tenant_id"],
                         "status": r["statusCode"], "served_tenant": body.get("tenant_id"),
                         "shipments": [s["shipment_id"] for s in body.get("shipments", [])]})
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    (outdir / "authorizer.log").write_text("\n".join(auth_lines) + "\n")
    (outdir / "requests.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    lines = [f"{'user':45} {'expected':18} {'status':6} served"]
    for r in rows:
        lines.append(f"{r['user']:45} {r['expected_tenant']:18} {r['status']:<6} {r['served_tenant']}")
    wrong = [r for r in rows if r["status"] == 200 and r["served_tenant"] != r["expected_tenant"]]
    lines.append(f"requests served another tenant's data: {len(wrong)} of {len(rows)}")
    (outdir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
