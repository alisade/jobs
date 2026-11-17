"""Build the CM-03 population from merged PRs and reconcile it to the prod deploy log. Do not edit
unless your fix needs it."""

from __future__ import annotations

import csv
import logging
import re
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("popexport.population")
DATA = Path(__file__).resolve().parents[1] / "data"
TZ = ZoneInfo("America/Chicago")
START, END = date(2026, 1, 1), date(2026, 6, 30)


def local_date(ts: str) -> date:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).astimezone(TZ).date()


def merged_in_period(pulls: list[dict]) -> list[dict]:
    out = []
    for p in pulls:
        if not p.get("merged_at") or p["base"]["ref"] != "main":
            continue
        if START <= local_date(p["merged_at"]) <= END:
            out.append(p)
    return out


def prod_changes_in_period() -> set[str]:
    with open(DATA / "deploys.csv", newline="") as f:
        return {r["change_id"] for r in csv.DictReader(f)
                if r["environment"] == "prod" and r["status"] == "succeeded" and START <= local_date(r["deployed_at"]) <= END}


def build(pulls: list[dict]) -> dict:
    merged = merged_in_period(pulls)
    ids = set()
    for p in merged:
        m = re.search(r"CHG-\d{6}", p["title"])
        if m:
            ids.add(m.group(0))
    deployed = prod_changes_in_period()
    missing = sorted(deployed - ids)
    result = {"period": f"{START}..{END}", "population": len(ids), "deploy_log_changes": len(deployed),
              "reconciled": ids == deployed, "missing_from_population": len(missing), "examples_missing": missing[:5]}
    log.info("population=%d deploy_log=%d reconciled=%s", result["population"], result["deploy_log_changes"], result["reconciled"])
    return result
