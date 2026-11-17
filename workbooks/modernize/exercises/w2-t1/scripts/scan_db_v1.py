#!/usr/bin/env python3
"""scan_db.py (frozen copy of the version used in the 2026-10-28 run; do not edit): list database touchpoints in a Java repository, for the reverse-engineer skill.

The agent calls this as a tool and reads stdout. Output is kept short so it does not flood the
context window.

Usage: scan_db.py <repo_root> [--limit N]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

EXTENSIONS = {".java", ".xml", ".properties", ".sql", ".sh"}
SKIP_DIRS = {".git", "target", "build", "node_modules"}
SQL = re.compile(r"\b(?:FROM|INTO|UPDATE|JOIN)\s+([A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)?)", re.IGNORECASE)
CALL = re.compile(r"\{\s*call\s+([A-Z][A-Z0-9_.]*)", re.IGNORECASE)
ORM_TABLE = re.compile(r"<table\s+name=\"([A-Za-z0-9_]+)\"")
SQL_KEYWORDS = {"SELECT", "WHERE", "SET", "VALUES", "DUAL"}


@dataclass(frozen=True)
class Hit:
    path: str      # relative to the repo root, forward slashes
    line: int      # 1-based
    table: str     # upper case, schema stripped
    text: str      # the source line, stripped


def module_of(path: str) -> str:
    return path.split("/", 1)[0]


def scan(root: Path) -> list[Hit]:
    hits: list[Hit] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in EXTENSIONS or SKIP_DIRS & set(p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        for n, line in enumerate(p.read_text(encoding="utf8", errors="replace").splitlines(), 1):
            names = SQL.findall(line) + CALL.findall(line) + ORM_TABLE.findall(line)
            for name in names:
                table = name.upper()
                if "." in table and not CALL.search(line):
                    table = table.split(".")[-1]
                if table in SQL_KEYWORDS:
                    continue
                hits.append(Hit(rel, n, table, line.strip()[:160]))
    return hits


def render(hits: list[Hit], limit: int = 200) -> str:
    lines = [f"{h.path}:{h.line}  {h.table}  {h.text}" for h in hits]
    return "\n".join(lines[:limit])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args(argv)
    print(render(scan(args.root), args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
