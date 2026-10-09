"""Run the suite and aggregate across repeated runs. Reference solution."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import comb
from typing import Any

from .checks import CHECKS, Check
from .judge import judge_check
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
    results = []
    for t in transcripts:
        outcome = [check(t) for check in checks]
        if judge_client is not None:
            outcome.append(judge_check(t, judge_client))
        results.append(RunResult(t.scenario, t.run, tuple(outcome)))
    return sorted(results, key=lambda r: (r.scenario, r.run))


def _validate(n: int, c: int, k: int) -> None:
    if n < 1 or not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError(f"need 1 <= k <= n and 0 <= c <= n (n={n}, c={c}, k={k})")


def pass_at_k(n: int, c: int, k: int) -> float:
    """P(at least one of k runs drawn without replacement passes) = 1 - C(n-c,k)/C(n,k)."""
    _validate(n, c, k)
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """P(all k runs drawn without replacement pass) = C(c,k)/C(n,k)."""
    _validate(n, c, k)
    return comb(c, k) / comb(n, k)


def scenario_stats(results: Sequence[RunResult], k: int) -> dict[str, ScenarioStats]:
    grouped: dict[str, list[RunResult]] = {}
    for r in results:
        grouped.setdefault(r.scenario, []).append(r)
    stats = {}
    for scenario in sorted(grouped):
        runs = grouped[scenario]
        n, c = len(runs), sum(r.passed for r in runs)
        stats[scenario] = ScenarioStats(
            n=n,
            c=c,
            pass_rate=c / n,
            pass_at_k=pass_at_k(n, c, k),
            pass_hat_k=pass_hat_k(n, c, k),
            flaky=0 < c < n,
        )
    return stats


def summarize(results: Sequence[RunResult], k: int) -> dict[str, Any]:
    stats = scenario_stats(results, k)
    failures = Counter(
        c.name for r in results for c in r.checks if not c.passed and not c.errored
    )
    return {
        "runs": len(results),
        "k": k,
        "pass_rate": round(sum(r.passed for r in results) / len(results), 4) if results else 0.0,
        "scenarios": {
            name: {
                "n": s.n,
                "c": s.c,
                "pass_rate": round(s.pass_rate, 4),
                "pass_at_k": round(s.pass_at_k, 4),
                "pass_hat_k": round(s.pass_hat_k, 4),
                "flaky": s.flaky,
            }
            for name, s in stats.items()
        },
        "flaky": sorted(n for n, s in stats.items() if s.flaky),
        "always_failing": sorted(n for n, s in stats.items() if s.c == 0),
        "failures_by_check": dict(sorted(failures.items())),
        "judge_errors": sum(1 for r in results for c in r.checks if c.errored),
    }
