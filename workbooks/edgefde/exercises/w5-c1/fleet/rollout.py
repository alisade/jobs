"""Model rollout controller: canary, phased batches, health gates, automatic rollback, resumable.

TODO: implement RolloutController (README "Your task"). The dataclasses below are the contract
the tests and scripts use; keep their names and fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .sim import Fleet


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

    def start(self, from_version: str, to_version: str) -> None:
        raise NotImplementedError("TODO")

    def run(self, max_windows: int = 500) -> RolloutReport:
        raise NotImplementedError("TODO")

    def report(self) -> RolloutReport:
        raise NotImplementedError("TODO")
