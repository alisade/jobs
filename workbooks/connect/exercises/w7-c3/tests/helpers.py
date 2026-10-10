"""Shared helpers for the w7-c3 tests: build a Firehose event, run the Lambda, load DuckDB."""
from __future__ import annotations

import base64
import csv
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if ROOT.name == "tests_hidden":  # pragma: no cover
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))


def load_module():
    import pipeline.transform as t

    return importlib.reload(t)


def sample_ctrs() -> list[dict]:
    return [json.loads(line) for line in (ROOT / "data" / "sample-ctrs.jsonl").read_text().splitlines() if line.strip()]


def firehose_event(ctrs: list, raw: list[bytes] | None = None) -> dict:
    records = []
    for i, c in enumerate(ctrs):
        payload = json.dumps(c).encode()
        records.append({"recordId": f"rec-{i:05d}", "approximateArrivalTimestamp": 1791900000000 + i, "data": base64.b64encode(payload).decode()})
    for j, r in enumerate(raw or []):
        records.append({"recordId": f"raw-{j:05d}", "approximateArrivalTimestamp": 1791900000000, "data": base64.b64encode(r).decode()})
    return {
        "invocationId": "c1d2e3f4-0000-4000-8000-000000000001",
        "deliveryStreamArn": "arn:aws:firehose:us-east-1:111122223333:deliverystream/lfg-connect-ctr",
        "region": "us-east-1",
        "records": records,
    }


def decoded_rows(result: dict) -> list[dict]:
    rows = []
    for r in result["records"]:
        if r["result"] == "Ok":
            rows.append(json.loads(base64.b64decode(r["data"])))
    return rows


def duck(rows: list[dict], sql_file: Path | None = None):
    import duckdb

    con = duckdb.connect()
    tmp = ROOT / ".duck-rows.jsonl"
    try:
        tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
        con.execute(f"CREATE TABLE contacts AS SELECT * FROM read_json_auto('{tmp}', format='newline_delimited')")
        # Athena/Glue declare dt as a string partition column; keep the same type here.
        con.execute("ALTER TABLE contacts ALTER dt TYPE VARCHAR")
    finally:
        tmp.unlink(missing_ok=True)
    con.execute("CREATE TABLE agent_staffing (agent_username VARCHAR, dt VARCHAR, staffed_seconds INTEGER)")
    with open(ROOT / "data" / "agent_staffing.csv") as f:
        con.executemany("INSERT INTO agent_staffing VALUES (?, ?, ?)", [(r["agent_username"], r["dt"], int(r["staffed_seconds"])) for r in csv.DictReader(f)])
    con.execute((sql_file or ROOT / "sql" / "kpis.sql").read_text())
    return con
