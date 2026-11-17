#!/usr/bin/env python3
"""Shared grading runner for the javaai Python exercises (called by each .grading/grade.sh).

Copies the exercise to a temp dir (the learner's folder is never written to), adds the
hidden tests from .grading/tests as tests_hidden/, runs pytest on the visible tests plus
the hidden ones under a wall-clock timeout, and prints one line per test followed by the
summary line the grader parses:

    GRADE_TESTS {"passed": <int>, "total": <int>}

``--expected-total`` keeps the denominator stable when the learner's code does not even
import (a collection error would otherwise report 0/1).

Exit code: 0 whenever the tests ran (failures are data); 2 when the harness itself broke.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

IGNORE = shutil.ignore_patterns(
    ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".hypothesis", "run", ".run",
    "node_modules", "*.pyc", "solution", "reference.md", "rubric.md",
)


def summary(passed: int, total: int) -> str:
    return "GRADE_TESTS " + json.dumps({"passed": passed, "total": total})


def first_line(text: str | None) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("E "):
            return line[2:].strip()[:160]
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()[:160]
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True, type=Path)
    ap.add_argument("--expected-total", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--visible", default="tests", help="visible tests dir, relative")
    ap.add_argument("--no-visible", action="store_true", help="hidden tests only")
    args = ap.parse_args()

    ex = args.exercise.resolve()
    hidden = ex / ".grading" / "tests"
    if not ex.is_dir():
        print(f"harness: exercise dir not found: {ex}")
        return 2

    with tempfile.TemporaryDirectory(prefix="javaai-grade-") as tmp:
        work = Path(tmp) / ex.name
        shutil.copytree(ex, work, ignore=IGNORE)
        # The copy keeps .grading/tests; the hidden tests run from tests_hidden/ instead.
        shutil.rmtree(work / ".grading", ignore_errors=True)
        targets: list[str] = []
        if not args.no_visible and (work / args.visible).is_dir():
            targets.append(args.visible)
        if hidden.is_dir() and any(hidden.glob("test_*.py")):
            shutil.copytree(hidden, work / "tests_hidden", ignore=IGNORE)
            targets.append("tests_hidden")
        if not targets:
            print("harness: no tests found")
            return 2

        junit = Path(tmp) / "junit.xml"
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["JAVAAI_GRADING"] = "1"
        env["JAVAAI_EXERCISE_SRC"] = str(ex)
        cmd = [
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "-o", "junit_family=xunit2", f"--junitxml={junit}", *targets,
        ]
        try:
            proc = subprocess.run(
                cmd, cwd=work, env=env, capture_output=True, text=True, timeout=args.timeout
            )
        except subprocess.TimeoutExpired:
            print(f"pytest exceeded {args.timeout}s and was stopped (a hang counts as failure)")
            print(summary(0, max(args.expected_total, 1)))
            return 0

        tail = (proc.stdout or "").strip().splitlines()[-25:]
        if not junit.exists():
            print("\n".join(tail))
            print((proc.stderr or "")[-2000:])
            print("harness: pytest produced no report")
            return 2

        cases = ET.parse(junit).getroot().iter("testcase")
        passed = total = 0
        lines = []
        for case in cases:
            total += 1
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            bad = case.find("failure")
            if bad is None:
                bad = case.find("error")
            skipped = case.find("skipped")
            if bad is not None:
                detail = first_line(bad.get("message")) or first_line(bad.text)
                lines.append(f"FAIL  {name}  -- {detail}")
            elif skipped is not None:
                lines.append(f"SKIP  {name}  (counts as not passed)")
            else:
                passed += 1
                lines.append(f"PASS  {name}")
        print("\n".join(lines))
        if total == 0 or proc.returncode not in (0, 1):
            print("\n".join(tail))
        total = max(total, args.expected_total)
        print(f"{passed}/{total} tests passed")
        print(summary(passed, total))
        return 0


if __name__ == "__main__":
    sys.exit(main())
