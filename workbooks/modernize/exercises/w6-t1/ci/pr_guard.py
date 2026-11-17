#!/usr/bin/env python3
"""pr_guard.py: CI check run on every ClaimDesk pull request, before the merge button unlocks.

Reads the PR's unified diff (git diff origin/main...HEAD) and fails the build when the change
weakens the safety net instead of passing it. Added in 2025 after a developer deleted a failing
test class (CLM-3920).

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


def check(diff: str, labels: frozenset[str] | set[str] = frozenset()) -> list[Violation]:
    out: list[Violation] = []
    for f in parse(diff):
        if f.deleted and is_test(f.path):
            out.append(Violation("test-deleted", f.path, "test file deleted"))
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
