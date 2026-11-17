"""Live alerting state and the audit log (do not edit). Thresholds drive the gateway alarms."""

from __future__ import annotations

THRESHOLDS = {"P04": {"outer_race": 12.0}, "P07": {"outer_race": 12.0}}
AUDIT: list[dict] = []


def audit(event: str, **fields) -> None:
    AUDIT.append({"event": event, **fields})


def set_threshold(machine: str, kind: str, db: float, actor: str) -> None:
    old = THRESHOLDS[machine][kind]
    THRESHOLDS[machine][kind] = float(db)
    audit("threshold_changed", machine=machine, kind=kind, old=old, new=float(db), actor=actor)


def reset() -> None:
    THRESHOLDS.clear()
    THRESHOLDS.update({"P04": {"outer_race": 12.0}, "P07": {"outer_race": 12.0}})
    AUDIT.clear()
