"""CM-03 population, completeness and accuracy checks, sample size and seeded selection."""

from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

INCLUDED_STATUSES = ("succeeded", "rolled_back")


@dataclass(frozen=True)
class PopulationItem:
    change_id: str
    pr_number: int
    repo: str
    first_deployed_at: str  # UTC ISO-8601 with Z
    local_date: str          # YYYY-MM-DD in the entity time zone
    deploy_count: int
    pr_merged_to_main: bool  # False is a finding to test, never a reason to drop the item


@dataclass
class Reconciliation:
    population_count: int
    control_total: int
    reconciled: bool
    differences: list[str] = field(default_factory=list)


def _utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def build_population(prs: list[dict], deploys: list[dict], period_start: date, period_end: date,
                     tz: str = "America/Chicago") -> list[PopulationItem]:
    zone = ZoneInfo(tz)
    by_pr = {p["number"]: p for p in prs}
    groups: dict[str, list[dict]] = {}
    for d in deploys:
        if d["environment"] != "prod" or d["status"] not in INCLUDED_STATUSES:
            continue
        local = _utc(d["deployed_at"]).astimezone(zone).date()
        if period_start <= local <= period_end:
            groups.setdefault(d["change_id"], []).append(d)
    out = []
    for cid, rows in groups.items():
        rows.sort(key=lambda r: _utc(r["deployed_at"]))
        first = rows[0]
        pr = by_pr.get(first["pr_number"])
        merged = bool(pr and pr.get("merged_at") and pr.get("base") == "main")
        ts = _utc(first["deployed_at"])
        out.append(PopulationItem(cid, first["pr_number"], first["repo"], ts.isoformat().replace("+00:00", "Z"),
                                  ts.astimezone(zone).date().isoformat(), len(rows), merged))
    return sorted(out, key=lambda i: i.change_id)


def completeness(population: list[PopulationItem], control_total: dict) -> Reconciliation:
    total = int(control_total["distinct_changes"])
    rec = Reconciliation(len(population), total, len(population) == total)
    if not rec.reconciled:
        rec.differences.append(f"population {len(population)} vs control total {total}")
    return rec


def accuracy_checks(population: list[PopulationItem], prs: list[dict], tickets: list[dict]) -> list[str]:
    """IPE accuracy: every item traces to a ticket and a PR, and the PR merged before the deploy."""
    by_pr = {p["number"]: p for p in prs}
    ticket_ids = {t["change_id"] for t in tickets}
    issues = []
    for i in population:
        if i.change_id not in ticket_ids:
            issues.append(f"{i.change_id}: no change ticket in the ticket export")
        pr = by_pr.get(i.pr_number)
        if pr is None:
            issues.append(f"{i.change_id}: PR {i.pr_number} not in the PR export")
            continue
        if pr.get("change_id") != i.change_id:
            issues.append(f"{i.change_id}: PR {i.pr_number} references {pr.get('change_id')}")
        if not i.pr_merged_to_main:
            issues.append(f"{i.change_id}: PR {i.pr_number} not merged to main")
        elif _utc(pr["merged_at"]) > _utc(i.first_deployed_at):
            issues.append(f"{i.change_id}: PR merged after the deploy")
    return issues


def sample_size(table: dict, frequency: str, risk: str = "standard") -> int:
    freqs = table["frequencies"]
    if frequency not in freqs:
        raise ValueError(f"unknown control frequency {frequency!r}; known: {', '.join(freqs)}")
    if risk not in freqs[frequency]:
        raise ValueError(f"unknown risk level {risk!r}")
    return int(freqs[frequency][risk])


def population_hash(population: list[PopulationItem]) -> str:
    ids = "\n".join(sorted(i.change_id for i in population))
    return hashlib.sha256(ids.encode()).hexdigest()


def select_sample(population: list[PopulationItem], n: int, seed: int) -> list[PopulationItem]:
    ordered = sorted(population, key=lambda i: i.change_id)
    if n >= len(ordered):
        return ordered
    idx = random.Random(seed).sample(range(len(ordered)), n)
    return [ordered[k] for k in idx]


def selection_log(population: list[PopulationItem], sample: list[PopulationItem], seed: int, size: int,
                  frequency: str, risk: str, rec: Reconciliation, issues: list[str]) -> dict:
    return {
        "control": "CM-03",
        "method": "simple random selection without replacement, random.Random(seed).sample over the population sorted by change_id",
        "seed": seed,
        "frequency": frequency,
        "risk": risk,
        "sample_size": size,
        "population_count": len(population),
        "population_sha256": population_hash(population),
        "completeness": asdict(rec),
        "accuracy_issues": issues,
        "selected": [i.change_id for i in sample],
    }
