"""Generate incident evidence for aiarch/x-1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""INC-20470  P2  Lighthouse session writes throttled every weekday around 09:00
Opened 2026-11-13 09:14 by AgentOps (K. Iyer)

Every weekday between 08:55 and 09:25 US Eastern, agents fail to register new sessions:
ThrottlingException on PutItem to lighthouse-sessions. Users see "assistant unavailable,
retry". The rest of the day is clean. Session volume tripled since the claims and
underwriting teams onboarded (2026-11-03).

On-call notes:
- 09:30 (D. Brandt) The table is on-demand, which should never throttle. Must be the new
  account-level table quota or the warm throughput. Proposing to set warm throughput to
  40,000 WCU on the table, or switch to provisioned with 20,000 WCU and autoscaling.
- 09:41 Base table ConsumedWriteCapacityUnits peaks at about 1,900 per minute. Nowhere near
  any limit.
""")
rows = ["timestamp,metric,dimensions,statistic,value"]
for m in range(50, 60):
    rows.append(f"2026-11-13T08:{m:02d}:00Z,ConsumedWriteCapacityUnits,TableName=lighthouse-sessions,Sum,{300 + m * 20}")
for m in range(0, 30, 5):
    rows.append(f"2026-11-13T09:{m:02d}:00Z,ConsumedWriteCapacityUnits,TableName=lighthouse-sessions,Sum,{1600 + m * 10}")
    rows.append(f"2026-11-13T09:{m:02d}:00Z,WriteThrottleEvents,TableName=lighthouse-sessions,Sum,0")
    rows.append(f"2026-11-13T09:{m:02d}:00Z,WriteThrottleEvents,TableName=lighthouse-sessions GlobalSecondaryIndexName=by-status,Sum,{900 + m * 40}")
    rows.append(f"2026-11-13T09:{m:02d}:00Z,OnlineIndexConsumedWriteCapacity,TableName=lighthouse-sessions GlobalSecondaryIndexName=by-status,Sum,{1600 + m * 10}")
(out / "cloudwatch-metrics.csv").write_text("\n".join(rows) + "\n")
(out / "describe-table.json").write_text(json.dumps({"Table": {
    "TableName": "lighthouse-sessions", "TableStatus": "ACTIVE", "BillingModeSummary": {"BillingMode": "PAY_PER_REQUEST"},
    "KeySchema": [{"AttributeName": "session_id", "KeyType": "HASH"}],
    "ItemCount": 1840211, "TableSizeBytes": 412339120,
    "GlobalSecondaryIndexes": [{"IndexName": "by-status", "IndexStatus": "ACTIVE",
        "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}, {"AttributeName": "started", "KeyType": "RANGE"}],
        "Projection": {"ProjectionType": "KEYS_ONLY"}, "ItemCount": 1839544}],
    "TimeToLiveDescription": {"TimeToLiveStatus": "ENABLED", "AttributeName": "ttl"}}}, indent=1) + "\n")
logs = []
for i in range(6):
    logs.append(json.dumps({"ts": f"2026-11-13T09:0{i}:12Z", "level": "ERROR", "op": "PutItem", "table": "lighthouse-sessions",
                            "error": "ThrottlingException",
                            "message": "Throughput exceeds the current capacity for one or more global secondary indexes. "
                                       "DynamoDB is automatically scaling your index so please try again shortly.",
                            "retries": 3}))
(out / "app-logs.jsonl").write_text("\n".join(logs) + "\n")
(out / "status-counts.txt").write_text("""status values on the base table (sampled scan, 2026-11-13 10:00):
  ACTIVE   1,839,102   (includes sessions closed by TTL-expired runtimes that never called close)
  CLOSED         442
""")
