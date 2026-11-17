"""Evaluate recorded agent runs against the test set and decide the release gate.

Implement the TODOs. The exact semantics are in README.md ("Metric definitions" and
"Gate rules"); the hidden tests follow them to the letter.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from release_gate.model import TestCase, load_testset

HIGHER_IS_BETTER = ("tool_accuracy", "grounded_rate", "refusal_recall", "fact_recall")
LOWER_IS_BETTER = ("over_refusal_rate",)
RELATIVE_LOWER_IS_BETTER = ("latency_p95_ms",)
METRICS = HIGHER_IS_BETTER + LOWER_IS_BETTER + RELATIVE_LOWER_IS_BETTER
EPS = 1e-9


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def load_transcripts(path: str | Path) -> tuple[dict[str, dict], list[str]]:
    """Return ({testCaseId: transcript}, errors).

    Must never raise on bad data: invalid JSON, a record without testCaseId or without an
    activities list, and duplicate testCaseIds (keep the first) each add one string to errors.
    A missing file returns ({}, [<one error>]).
    """
    # TODO
    raise NotImplementedError


def normalize(text: str) -> str:
    """Lowercase, replace every run of non [a-z0-9] characters with one space, strip."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def p95(values: list[int]) -> int | None:
    """Nearest-rank 95th percentile; None for an empty list."""
    # TODO
    raise NotImplementedError


def score_case(case: TestCase, transcript: dict | None, markers: list[str]) -> dict:
    """Score one test case. See README for the per-case result keys and rules."""
    # TODO
    raise NotImplementedError


def evaluate_run(cases: list[TestCase], run_dir: str | Path, config: dict) -> dict:
    """Load <run_dir>/transcripts.jsonl and return the run report (cases, metrics,
    categories, missing, errors)."""
    # TODO
    raise NotImplementedError


def compare_runs(baseline: dict, candidate: dict, config: dict) -> dict:
    """Return {"deltas": {...}, "regressions": [...], "case_regressions": [...]}."""
    # TODO
    raise NotImplementedError


def gate(candidate: dict, comparison: dict | None, config: dict) -> dict:
    """Return {"passed": bool, "reasons": [str, ...]}."""
    # TODO
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """CLI. Exit 0 = gate passed, 1 = gate failed, 2 = bad input (unreadable test set/config)."""
    ap = argparse.ArgumentParser(prog="release_gate")
    ap.add_argument("--testset", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # TODO: load inputs, evaluate both runs, compare, gate, write the JSON report to --out,
    # print a one-line verdict plus reasons, return the exit code.
    raise NotImplementedError
