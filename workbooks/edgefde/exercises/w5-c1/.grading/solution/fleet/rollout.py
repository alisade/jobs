"""Model rollout controller: canary, phased batches, health gates, automatic rollback, resumable."""

from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .sim import Fleet, Health


@dataclass(frozen=True)
class Policy:
    phases: tuple = (1, 0.2, 0.5, 1.0)  # int = device count, float = fraction of the fleet (cumulative)
    healthy_windows: int = 3
    max_error_rate: float = 0.02
    max_p95_ms: float = 50.0
    max_alert_ratio: float = 3.0
    offline_timeout_windows: int = 6
    max_concurrent: int = 3
    rollback_timeout_windows: int = 20


class RolloutInProgress(RuntimeError):
    pass


@dataclass
class RolloutReport:
    status: str  # "in_progress" | "succeeded" | "rolled_back"
    from_version: str
    to_version: str
    updated: list[str] = field(default_factory=list)
    rolled_back: list[str] = field(default_factory=list)
    skipped_offline: list[str] = field(default_factory=list)
    failed_phase: int | None = None
    reason: str | None = None
    windows: int = 0


class RolloutController:
    def __init__(self, fleet: Fleet, state_path: str | Path, policy: Policy = Policy()) -> None:
        self.fleet, self.path, self.policy = fleet, Path(state_path), policy
        self.s: dict | None = json.loads(self.path.read_text()) if self.path.exists() else None

    # ---- persistence -----------------------------------------------------------------
    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.s, indent=1, sort_keys=True))
        os.replace(tmp, self.path)  # atomic: a crash never leaves half a state file

    # ---- api -------------------------------------------------------------------------
    def start(self, from_version: str, to_version: str) -> None:
        if self.s and self.s["status"] == "in_progress":
            raise RolloutInProgress(f"rollout {self.s['from']} -> {self.s['to']} is still in progress")
        sample = self.fleet.tick()
        rates = [h.alert_rate for h in sample.values() if h and h.version == from_version]
        online = [d for d in self.fleet.ids() if sample.get(d) is not None]
        if not online:
            raise RuntimeError("no online device for a canary")
        canary = online[0]
        order = [canary] + [d for d in self.fleet.ids() if d != canary]
        n = len(order)
        counts = []
        for p in self.policy.phases:
            c = p if isinstance(p, int) else math.ceil(p * n)
            counts.append(max(1, min(n, c)))
        self.s = {
            "status": "in_progress", "from": from_version, "to": to_version, "order": order,
            "counts": counts, "phase": 0, "touched": [], "skipped": [], "offline": {}, "streak": {},
            "baseline_alert_rate": statistics.median(rates) if rates else 0.0,
            "failed_phase": None, "reason": None, "rolled_back": [], "windows": 0,
        }
        self._save()

    def _unhealthy(self, h: Health) -> str | None:
        p = self.policy
        if not h.up:
            return f"{h.device_id}: process down"
        if h.error_rate > p.max_error_rate:
            return f"{h.device_id}: inference error rate {h.error_rate:.3f} > {p.max_error_rate}"
        if h.p95_ms > p.max_p95_ms:
            return f"{h.device_id}: p95 latency {h.p95_ms:.1f} ms > {p.max_p95_ms}"
        limit = p.max_alert_ratio * max(self.s["baseline_alert_rate"], 0.005)
        if h.alert_rate > limit:
            return f"{h.device_id}: alert rate {h.alert_rate:.3f} > {limit:.3f} ({p.max_alert_ratio}x baseline)"
        return None

    def _rollback(self, reason: str) -> None:
        s = self.s
        s["reason"], s["failed_phase"] = reason, s["phase"]
        for d in s["touched"]:
            self.fleet.set_desired(d, s["from"])
        s["rolled_back"] = list(s["touched"])
        for _ in range(self.policy.rollback_timeout_windows):
            rep = self.fleet.tick()
            s["windows"] += 1
            if all(rep.get(d) is None or rep[d].version == s["from"] for d in s["touched"]):
                break
        s["status"] = "rolled_back"
        self._save()

    def run(self, max_windows: int = 500) -> RolloutReport:
        if not self.s:
            raise RuntimeError("call start() first")
        s, p = self.s, self.policy
        for _ in range(max_windows):
            if s["status"] != "in_progress":
                break
            phase_devs = s["order"][: s["counts"][s["phase"]]]
            last = self.fleet.last
            in_flight = [d for d in s["touched"] if d not in s["skipped"]
                         and (last.get(d) is None or last[d].version != s["to"])]
            for d in phase_devs:
                if len(in_flight) >= p.max_concurrent:
                    break
                if d not in s["touched"] and d not in s["skipped"]:
                    self.fleet.set_desired(d, s["to"])
                    s["touched"].append(d)
                    in_flight.append(d)
            rep = self.fleet.tick()
            s["windows"] += 1
            for d in list(s["touched"]):
                if d in s["skipped"]:
                    continue
                h = rep.get(d)
                if h is None:
                    s["offline"][d] = s["offline"].get(d, 0) + 1
                    s["streak"][d] = 0
                    if s["offline"][d] > p.offline_timeout_windows:
                        s["skipped"].append(d)
                        self.fleet.set_desired(d, s["from"])  # comes back on the old, known-good model
                    continue
                s["offline"][d] = 0
                if h.version != s["to"]:
                    continue
                bad = self._unhealthy(h)
                if bad:
                    self._rollback(bad)
                    return self.report()
                s["streak"][d] = s["streak"].get(d, 0) + 1
            done = all(d in s["skipped"] or (d in s["touched"] and s["streak"].get(d, 0) >= p.healthy_windows)
                       for d in phase_devs)
            if done:
                if s["phase"] == len(s["counts"]) - 1:
                    s["status"] = "succeeded"
                else:
                    s["phase"] += 1
            self._save()
        return self.report()

    def report(self) -> RolloutReport:
        s = self.s
        updated = [d for d in s["touched"] if d not in s["skipped"]] if s["status"] != "rolled_back" else []
        return RolloutReport(s["status"], s["from"], s["to"], updated, list(s["rolled_back"]),
                             list(s["skipped"]), s["failed_phase"], s["reason"], s["windows"])
