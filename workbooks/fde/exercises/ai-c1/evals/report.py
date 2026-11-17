"""Run the suite and aggregate across repeated runs.

YOUR WORK GOES HERE. README.md defines pass@k and pass^k (unbiased estimators over n runs
with c passes) and the summary dict's exact keys.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from .checks import CHECKS, Check
from .judge import judge_check  # noqa: F401
from .transcript import CheckResult, Transcript


@dataclass(frozen=True)
class RunResult:
    scenario: str
    run: int
    checks: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


@dataclass(frozen=True)
class ScenarioStats:
    n: int
    c: int
    pass_rate: float
    pass_at_k: float
    pass_hat_k: float
    flaky: bool


def run_suite(
    transcripts: Iterable[Transcript],
    checks: Sequence[Check] = CHECKS,
    judge_client: Any = None,
) -> list[RunResult]:
    """Every check on every transcript (plus judge_check when a client is given), sorted
    by (scenario, run)."""
    raise NotImplementedError("run_suite")


def pass_at_k(n: int, c: int, k: int) -> float:
    raise NotImplementedError("pass_at_k")


def pass_hat_k(n: int, c: int, k: int) -> float:
    raise NotImplementedError("pass_hat_k")


def scenario_stats(results: Sequence[RunResult], k: int) -> dict[str, ScenarioStats]:
    raise NotImplementedError("scenario_stats")


def summarize(results: Sequence[RunResult], k: int) -> dict[str, Any]:
    raise NotImplementedError("summarize")
