#!/usr/bin/env python3
"""pr_guard.py: CI check run on every ClaimDesk pull request, before the merge button unlocks.

Reads the PR's unified diff (git diff origin/main...HEAD) and fails the build when the change
weakens the safety net instead of passing it. Added in 2025 after a developer deleted a failing
test class (CLM-3920); extended after INC-7790 (PR #1187), where an agent made CI green by
regenerating golden files and disabling a failing test. Rules:

  golden-changed      a golden/approved file changed without the approved-golden-change label
  test-disabled       a skip/disable marker was added to a test file
  test-deleted        a test file was deleted
  assertion-removed   a test file lost assertion lines (net of the ones added)
  test-count-dropped  fewer test methods after the change than before (net, across all files)

Usage: pr_guard.py <diff_file> [--label NAME ...]
Exit 0 when clean, 1 when there are violations (printed one per line), 2 on bad input.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

TEST_PATH = re.compile(r"(^|/)src/test/|(^|/)tests?/|Test\.java$|Tests\.cs$|(^|/)test_[^/]*\.py$")
# Golden masters and approval files: the contract with partners. Changing them needs a human decision.
GOLDEN_PATH = re.compile(r"(^|/)golden/|(^|/)approved/|\.approved\.[^/]+$|\.received\.[^/]+$")
GOLDEN_LABEL = "approved-golden-change"
SKIP_MARKERS = re.compile(
    r"@Disabled\b|@Ignore\b|@DisabledIf|@EnabledIf|pytest\.mark\.skip|pytest\.mark\.xfail|pytest\.skip\(|unittest\.skip"
    r"|\bSkip\s*=|\bxit\(|\bit\.skip\(|\bdescribe\.skip\(|\btest\.skip\(|Assumptions\.assume")
ASSERTION = re.compile(r"\bassert\w*\s*\(|\bassert\s|\bAssert\.\w+\(|\bexpect\(|\bverify\(|\bfail\(|\bassertThat\(|\bassertThrows\(")
TEST_MARKER = re.compile(r"@Test\b|@ParameterizedTest\b|@RepeatedTest\b|@TestFactory\b|^\s*def test_|^\s*async def test_|\[Fact\b|\[Theory\b|\bit\(\s*['\"]|\btest\(\s*['\"]")


@dataclass(frozen=True)
class Violation:
    rule: str      # golden-changed | test-disabled | test-deleted | assertion-removed | test-count-dropped
    path: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.path}: {self.detail}"


@dataclass
class FileDiff:
    old_path: str | None
    new_path: str | None
    deleted: bool = False
    added: list[str] | None = None
    removed: list[str] | None = None

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or "?"


def parse(diff: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(\S+) b/(\S+)", line)
            cur = FileDiff(m.group(1), m.group(2), added=[], removed=[]) if m else FileDiff(None, None, added=[], removed=[])
            files.append(cur)
        elif cur is None:
            continue
        elif line.startswith("deleted file mode"):
            cur.deleted = True
        elif line.startswith("--- ") or line.startswith("+++ "):
            continue
        elif line.startswith("+"):
            cur.added.append(line[1:])
        elif line.startswith("-"):
            cur.removed.append(line[1:])
    return files


def is_test(path: str) -> bool:
    return bool(TEST_PATH.search(path))


def _code(line: str) -> str:
    """The line without a trailing // or # comment, so commented-out code does not count."""
    stripped = line.strip()
    if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("*") or stripped.startswith("/*"):
        return ""
    return line


def _count(pattern: re.Pattern, lines: list[str]) -> int:
    return sum(1 for l in lines if pattern.search(_code(l)))


def check(diff: str, labels: frozenset[str] | set[str] = frozenset()) -> list[Violation]:
    """Every rule, every file. Returns all violations (not just the first) so the report is complete."""
    out: list[Violation] = []
    tests_added = tests_removed = 0
    for f in parse(diff):
        paths = {p for p in (f.old_path, f.new_path) if p}
        if any(GOLDEN_PATH.search(p) for p in paths) and (f.added or f.removed or f.deleted):
            if GOLDEN_LABEL not in labels:
                out.append(Violation("golden-changed", f.path,
                                     f"golden/approved file changed (+{len(f.added)} -{len(f.removed)}) without the '{GOLDEN_LABEL}' label"))
            continue
        if not any(is_test(p) for p in paths):
            continue
        if f.deleted:
            out.append(Violation("test-deleted", f.path, "test file deleted"))
        for line in f.added:
            if SKIP_MARKERS.search(_code(line)):
                out.append(Violation("test-disabled", f.path, f"skip marker added: {line.strip()[:100]}"))
        lost = _count(ASSERTION, f.removed) - _count(ASSERTION, f.added)
        if lost > 0:
            out.append(Violation("assertion-removed", f.path, f"{lost} assertion line(s) removed net"))
        tests_added += _count(TEST_MARKER, f.added)
        tests_removed += _count(TEST_MARKER, f.removed)
    if tests_removed > tests_added:
        out.append(Violation("test-count-dropped", "(all test files)",
                             f"{tests_removed - tests_added} fewer test(s): -{tests_removed} +{tests_added}"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("diff", type=Path)
    ap.add_argument("--label", action="append", default=[])
    args = ap.parse_args(argv)
    if not args.diff.is_file():
        print(f"pr_guard: no such diff file {args.diff}", file=sys.stderr)
        return 2
    violations = check(args.diff.read_text(encoding="utf8", errors="replace"), frozenset(args.label))
    for v in violations:
        print(v)
    print(f"pr_guard: {len(violations)} violation(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
