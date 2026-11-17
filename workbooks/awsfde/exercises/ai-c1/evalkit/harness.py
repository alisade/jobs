"""Run the golden cases over recorded runs, build the report, gate the release."""

from __future__ import annotations

from typing import Callable

from .checks import ALL

Judge = Callable[[dict, dict], bool]


def evaluate(golden: list[dict], runs: list[dict], judge: Judge | None = None) -> dict:
    """TODO: see README."""
    raise NotImplementedError



def regressions(baseline: dict, candidate: dict) -> list[str]:
    """TODO: see README."""
    raise NotImplementedError



def gate(report: dict, baseline: dict | None = None, min_pass_rate: float = 0.9) -> tuple[bool, list[str]]:
    """TODO: see README."""
    raise NotImplementedError
