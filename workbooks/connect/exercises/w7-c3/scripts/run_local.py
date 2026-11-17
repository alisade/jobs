"""End-to-end local run: sample CTRs -> Firehose event -> transform -> out/ partitioned like S3 ->
DuckDB views from sql/kpis.sql. Mirrors s3://lfg-connect-lake/ctr/channel=.../dt=.../retention=.../"""
import base64
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "tests"))
from helpers import duck, firehose_event, sample_ctrs  # noqa: E402
from pipeline.transform import lambda_handler  # noqa: E402

result = lambda_handler(firehose_event(sample_ctrs(), raw=[b"not json"]), None)
counts = {}
out = root / "out"
shutil.rmtree(out, ignore_errors=True)
rows = []
for r in result["records"]:
    counts[r["result"]] = counts.get(r["result"], 0) + 1
    if r["result"] != "Ok":
        continue
    keys = (r.get("metadata") or {}).get("partitionKeys") or {}
    part = out.joinpath(*[f"{k}={v}" for k, v in keys.items()]) if keys else out / "unpartitioned"
    part.mkdir(parents=True, exist_ok=True)
    line = base64.b64decode(r["data"]).decode()
    with open(part / "part-0000.json", "a") as f:
        f.write(line if line.endswith("\n") else line + "\n")
    rows.append(json.loads(line))
print("results:", counts)
print("partitions:", sorted(str(p.relative_to(out)) for p in out.rglob("part-0000.json"))[:8], "...")
con = duck(rows)
for view in ("queue_daily", "agent_occupancy", "containment_by_intent"):
    try:
        print(f"\n== {view}")
        print(con.execute(f"SELECT * FROM {view} ORDER BY 1, 2 LIMIT 12").fetchdf().to_string(index=False))
    except Exception as e:  # missing view in the starter
        print(f"  ({e.__class__.__name__}: {str(e).splitlines()[0]})")
