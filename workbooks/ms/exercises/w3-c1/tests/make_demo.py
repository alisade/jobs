"""make demo: build a fragmented demo lakehouse with a maintenance.json config."""

import json
import os
import shutil
import sys

from helpers import big_files, fragmented

root = sys.argv[1] if len(sys.argv) > 1 else "demo"
shutil.rmtree(root, ignore_errors=True)
os.makedirs(root)
fragmented(f"{root}/Tables/telemetry_readings", files=40, rows=30)
fragmented(f"{root}/Tables/trip_events", files=12, rows=30, partitioned=True, regions=("EU", "US"))
big_files(f"{root}/Tables/dim_vehicle", files=2)
cfg = {
    "tables": {
        "telemetry_readings": {"path": f"{root}/Tables/telemetry_readings", "zorder": ["vehicle_id"]},
        "trip_events": {"path": f"{root}/Tables/trip_events"},
        "dim_vehicle": {"path": f"{root}/Tables/dim_vehicle"},
    },
    "policy": {"small_file_bytes": 1048576, "min_files": 8, "small_file_ratio": 0.5, "vacuum_retention_hours": 168},
}
with open(f"{root}/maintenance.json", "w") as f:
    json.dump(cfg, f, indent=2)
print(f"demo lakehouse in {root}/")
