"""Generate the synthetic Q4 case export (fixed seed) and the external audit sample.

python scripts/generate.py data
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ZONES = ["America/New_York", "America/Chicago", "America/Denver"]
LOBS = ["medicare-advantage"] * 5 + ["medicaid-mco"] * 3 + ["chip-mco"] + ["commercial"] * 3


def calendar_due(received: datetime, priority: str, tz: str) -> datetime:
    if priority == "expedited":
        return received.astimezone(UTC) + timedelta(hours=72)
    z = ZoneInfo(tz)
    loc = received.astimezone(z)
    return (loc.replace(tzinfo=None) + timedelta(days=7)).replace(tzinfo=z).astimezone(UTC)


def main(out_dir: str) -> None:
    rng = random.Random(20261113)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 10, 1, tzinfo=UTC)
    rows = []
    for i in range(1, 641):
        tz = rng.choice(ZONES)
        received = (start + timedelta(minutes=rng.randrange(0, 60 * 24 * 52))).astimezone(ZoneInfo(tz))
        priority = "expedited" if rng.random() < 0.22 else "standard"
        lob = rng.choice(LOBS)
        r = rng.random()
        if priority == "expedited":
            hours = rng.uniform(73, 95) if r < 0.04 else rng.uniform(4, 70)
            decided = received + timedelta(hours=hours)
        else:
            if r < 0.07:
                decided = calendar_due(received, priority, tz).astimezone(ZoneInfo(tz)) + timedelta(hours=rng.uniform(2, 40))
            else:
                decided = received + timedelta(hours=rng.uniform(6, 160))
        rows.append({
            "case_id": f"PA-2026-{i:05d}", "lob": lob, "priority": priority, "plan_tz": tz,
            "received_at": received.isoformat(timespec="seconds"),
            "decided_at": decided.astimezone(ZoneInfo(tz)).isoformat(timespec="seconds"),
            "decision": rng.choice(["approved"] * 7 + ["denied", "pended"]),
        })
    with open(out / "cases.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    late_std = [r for r in rows if r["priority"] == "standard" and r["lob"] != "commercial"
                and datetime.fromisoformat(r["decided_at"]) > calendar_due(datetime.fromisoformat(r["received_at"]), "standard", r["plan_tz"])]
    sample = rng.sample(late_std, 5)
    with open(out / "audit_sample.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["case_id", "auditor_finding"])
        for r in sorted(sample, key=lambda x: x["case_id"]):
            w.writerow([r["case_id"], "standard decision issued after day 7 (calendar) from receipt"])
    print(f"wrote {len(rows)} cases to {out / 'cases.csv'}; audit sample of {len(sample)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
