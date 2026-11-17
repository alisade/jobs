"""Generate the incident bundle in incident/ by replaying the morning's events
through the ingestion mapping that is DEPLOYED in production (captured below
from `.show table TelemetryLanding ingestion json mappings`), not the file you
are editing. Re-running is idempotent.
"""

import datetime as dt
import json
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "incident"

DEPLOYED_MAPPING = [
    {"Column": "Timestamp", "DataType": "datetime", "Properties": {"Path": "$.ts"}},
    {"Column": "DeviceId", "DataType": "string", "Properties": {"Path": "$.deviceId"}},
    {"Column": "VehicleId", "DataType": "string", "Properties": {"Path": "$.vehicleId"}},
    {"Column": "SpeedKph", "DataType": "real", "Properties": {"Path": "$.speedKph"}},
    {"Column": "EngineTempC", "DataType": "real", "Properties": {"Path": "$.engineTempC"}},
    {"Column": "FuelPct", "DataType": "real", "Properties": {"Path": "$.fuelPct"}},
    {"Column": "FirmwareVersion", "DataType": "string", "Properties": {"Path": "$.fw"}},
]

DAY = dt.datetime(2026, 10, 20, tzinfo=dt.timezone.utc)
START = DAY.replace(hour=9, minute=20)
CUTOVER = DAY.replace(hour=9, minute=40)
END = DAY.replace(hour=10, minute=10)
VEHICLES = [(f"TRK-{100 + i}", f"dev-{0x9f1 + i * 37:03x}") for i in range(8)] + \
           [("VAN-201", "dev-c33"), ("VAN-202", "dev-c71")]


def gen_events():
    rnd = random.Random(42)
    events = []
    t = START
    while t < END:
        for veh, dev in VEHICLES:
            ts = t + dt.timedelta(milliseconds=rnd.randint(0, 19_999))
            speed = round(max(0.0, rnd.gauss(52, 18)), 1)
            temp = round(rnd.gauss(88, 4), 1)
            fuel = round(rnd.uniform(20, 95), 1)
            if t < CUTOVER:
                ev = {"deviceId": dev, "vehicleId": veh,
                      "ts": ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z",
                      "speedKph": speed, "engineTempC": temp, "fuelPct": fuel, "fw": "4.1.7"}
            else:
                ev = {"schemaVersion": 2, "device": {"id": dev, "fw": "4.2.0"}, "vehicleId": veh,
                      "tsMs": int(ts.timestamp() * 1000),
                      "telemetry": {"speedKph": speed, "engineTempC": temp, "fuelPct": fuel}}
            events.append((ts, ev))
        t += dt.timedelta(seconds=20)
    return events


def bin5(d):
    return d.replace(minute=d.minute - d.minute % 5, second=0, microsecond=0)


def w(name, text):
    (OUT / name).write_text(text.rstrip("\n") + "\n")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    cols = sim.load_schema()["TelemetryLanding"]
    events = gen_events()
    landed = []
    for ts, ev in events:
        row = sim.apply_mapping(ev, DEPLOYED_MAPPING, cols)
        ing = ts + dt.timedelta(seconds=4)
        landed.append((ing, row))

    w("PAGER.txt", """\
[P2] FleetOps live dashboard - no data
Opened 2026-10-20 10:07 UTC by Priya N. (dispatch lead), routed to data-platform on-call

"The live fleet map and the speed tiles have been flat since about 09:40. Vehicles are definitely
moving (drivers are calling in). The overheating alerts have also gone quiet, which is scary.
Eventstream page shows events flowing, so I don't think it's the trucks."

Linked: dashboard 'FleetOps Live' (reads TelemetryEnriched), Activator rule 'Engine overheating'.
""")

    # Eventstream metrics, per minute
    lines = ["Minute(UTC),IncomingMessages,Outgoing_eh-fleet/TelemetryLanding,Outgoing_lh_fleet_raw,DataConversionErrors,RuntimeErrors"]
    per_min = {}
    for ts, _ in events:
        k = ts.replace(second=0, microsecond=0)
        per_min[k] = per_min.get(k, 0) + 1
    for k in sorted(per_min):
        n = per_min[k]
        lines.append(f"{k:%H:%M},{n},{n},{n},0,0")
    w("eventstream_metrics.csv", "\n".join(lines))

    # Landing vs enriched counts
    agg = {}
    for ing, row in landed:
        k = bin5(ing)
        a = agg.setdefault(k, [0, 0, 0, 0, 0])
        a[0] += 1
        ok = bool(row["DeviceId"]) and row["Timestamp"] is not None
        a[1] += 1 if ok else 0
        a[2] += 0 if row["DeviceId"] else 1
        a[3] += 1 if row["Timestamp"] is None else 0
        a[4] += 1 if row["SpeedKph"] is None else 0
    out = ["// fleet KQL queryset, run 10:12 UTC by on-call",
           "union withsource=T TelemetryLanding, TelemetryEnriched",
           "| where ingestion_time() between (datetime(2026-10-20 09:20) .. datetime(2026-10-20 10:10))",
           "| summarize Rows = count() by T, Bin = bin(ingestion_time(), 5m)",
           "| evaluate pivot(T, sum(Rows))", "",
           "Bin                  | TelemetryEnriched | TelemetryLanding",
           "---------------------+-------------------+-----------------"]
    for k in sorted(agg):
        out.append(f"{k:%Y-%m-%d %H:%M}     | {agg[k][1]:>17} | {agg[k][0]:>16}")
    w("kql_01_landing_vs_enriched.txt", "\n".join(out))

    out = ["TelemetryLanding",
           "| where ingestion_time() between (datetime(2026-10-20 09:20) .. datetime(2026-10-20 10:10))",
           "| summarize Rows = count(), EmptyDeviceId = countif(isempty(DeviceId)),",
           "            NullTimestamp = countif(isnull(Timestamp)), NullSpeed = countif(isnull(SpeedKph))",
           "    by Bin = bin(ingestion_time(), 5m)", "",
           "Bin              | Rows | EmptyDeviceId | NullTimestamp | NullSpeed",
           "-----------------+------+---------------+---------------+----------"]
    for k in sorted(agg):
        a = agg[k]
        out.append(f"{k:%Y-%m-%d %H:%M} | {a[0]:>4} | {a[2]:>13} | {a[3]:>13} | {a[4]:>9}")
    w("kql_02_landing_null_profile.txt", "\n".join(out))

    before = [r for i, r in landed if i < CUTOVER][-3:]
    after = [r for i, r in landed if i >= CUTOVER + dt.timedelta(minutes=5)][:3]
    w("kql_03_landing_sample_rows.txt",
      "TelemetryLanding | where ingestion_time() between (datetime(2026-10-20 09:39:30) .. datetime(2026-10-20 09:39:59)) | take 3\n\n"
      + sim.table(before, cols)
      + "\n\nTelemetryLanding | where ingestion_time() > datetime(2026-10-20 09:45) | take 3\n\n"
      + sim.table(after, cols))

    w("kql_04_show_ingestion_failures.txt", """\
.show ingestion failures
| where FailedOn > datetime(2026-10-20 09:00)
| where Table in ("TelemetryLanding", "TelemetryEnriched") or OriginatesFromUpdatePolicy == true

(no rows)
""")

    mapping_line = json.dumps(DEPLOYED_MAPPING, separators=(",", ":"))
    w("kql_05_show_mappings.txt",
      ".show table TelemetryLanding ingestion json mappings\n\n"
      "Name                     | Kind | Mapping | LastUpdatedOn | Database | Table\n"
      f"TelemetryLanding_mapping | Json | {mapping_line} | 2026-08-14 16:02:11 | fleet | TelemetryLanding\n")

    w("kql_06_update_policy.txt", """\
.show table TelemetryEnriched policy update

EntityName                 | Policy
[fleet].[TelemetryEnriched] | [{"IsEnabled":true,"Source":"TelemetryLanding","Query":"EnrichTelemetry()","IsTransactional":true,"PropagateIngestionProperties":false,"ManagedIdentity":null}]

.show function EnrichTelemetry | project Name, Folder, DocString
EnrichTelemetry | UpdatePolicies | Data-quality filter and enrichment for TelemetryLanding
""")

    pre = [e for t, e in events if t < CUTOVER][-4:]
    post = [e for t, e in events if t >= CUTOVER][:4]
    w("eventstream_data_preview.jsonl",
      "\n".join(json.dumps(e) for e in pre + post))

    w("capacity_metrics.txt", """\
Fabric Capacity Metrics app - capacity 'fleet-prod-f16' (F16), 2026-10-20 UTC

Time   | CU % (smoothed) | Interactive delay | Interactive rejection | Background rejection | Top item
09:00  |  58%            | no                | no                    | no                   | eh-fleet (Eventhouse)
09:10  |  97%            | no                | no                    | no                   | nb_backfill_trips (Notebook)
09:15  | 104%            | YES (20 s)        | no                    | no                   | nb_backfill_trips (Notebook)
09:20  | 101%            | YES (20 s)        | no                    | no                   | nb_backfill_trips (Notebook)
09:25  |  83%            | no                | no                    | no                   | nb_backfill_trips (Notebook)
09:30  |  64%            | no                | no                    | no                   | eh-fleet (Eventhouse)
09:45  |  57%            | no                | no                    | no                   | eh-fleet (Eventhouse)
10:00  |  55%            | no                | no                    | no                   | eh-fleet (Eventhouse)

Note from #fabric-capacity (09:31): "backfill notebook finished, we're back under 100%."
""")

    w("telemetry-gateway_git_log.txt", """\
$ git -C telemetry-gateway log --since=2026-10-19 -p --stat -- src/
commit 7c2e9a41f0d3b8e5a6c1d2f3e4a5b6c7d8e9f0a1 (tag: v4.2.0, origin/main)
Author: Marco Bianchi <marco.bianchi@contoso-fleet.example>
Date:   Mon Oct 20 09:31:07 2026 +0000

    release 4.2.0: envelope v2 (#812)

    - group device metadata under `device`
    - epoch-millisecond timestamps (cheaper to produce on the edge, no clock string formatting)
    - sensor values under `telemetry`
    Consumers: same fields, just reorganised. Rollout via deploy pipeline at 09:38.

 src/serializer.ts | 23 ++++++++++++++---------
 1 file changed, 14 insertions(+), 9 deletions(-)

diff --git a/src/serializer.ts b/src/serializer.ts
@@ -12,18 +12,23 @@ export function toEvent(r: Reading, d: DeviceInfo): object {
-  return {
-    deviceId: d.id,
-    vehicleId: r.vehicleId,
-    ts: new Date(r.epochMs).toISOString(),
-    speedKph: r.speedKph,
-    engineTempC: r.engineTempC,
-    fuelPct: r.fuelPct,
-    fw: d.firmware,
-  };
+  return {
+    schemaVersion: 2,
+    device: { id: d.id, fw: d.firmware },
+    vehicleId: r.vehicleId,
+    tsMs: r.epochMs,
+    telemetry: {
+      speedKph: r.speedKph,
+      engineTempC: r.engineTempC,
+      fuelPct: r.fuelPct,
+    },
+  };
 }

commit 19ab0c4de5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
Author: Sam Okafor <sam.okafor@contoso-fleet.example>
Date:   Sun Oct 19 22:14:51 2026 +0000

    chore: bump @azure/event-hubs to 6.0.1 (#809)

 package.json | 2 +-
""")

    w("activator_rule_status.txt", """\
Activator 'fleet-alerts' / rule 'Engine overheating' (source: TelemetryEnriched, every 1 min)
Status: Running
Last event evaluated: 2026-10-20 09:39:58 UTC
Warning: no new events in the last 30 minutes.
Alerts fired today: 2 (08:51 TRK-104, 09:22 TRK-106)
""")
    print(f"incident bundle written to {OUT.relative_to(HERE)}/ ({len(list(OUT.iterdir()))} files)")


if __name__ == "__main__":
    main()
