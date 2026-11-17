#!/usr/bin/env python3
"""scan_db.py: list database touchpoints in a Java repository, for the reverse-engineer skill.

The agent calls this as a tool and reads stdout. Output is kept short so it does not flood the
context window.

The summary (every table, count, modules) is always complete; the hit list is paged and says
when it is cut, so the agent can never mistake a page for the whole answer.

Usage: scan_db.py <repo_root> [--limit N] [--offset K]
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


def summarize(hits: list[Hit]) -> dict[str, dict]:
    """Every distinct table with its hit count and modules. Always complete, whatever the page size."""
    out: dict[str, dict] = {}
    for h in hits:
        e = out.setdefault(h.table, {"count": 0, "modules": set()})
        e["count"] += 1
        e["modules"].add(module_of(h.path))
    return {t: {"count": e["count"], "modules": sorted(e["modules"])} for t, e in sorted(out.items())}


def render(hits: list[Hit], limit: int = 200, offset: int = 0) -> str:
    """One page of hits. The header always states the total; a cut page says so on its last line."""
    total = len(hits)
    page = hits[offset:offset + limit]
    first, last = (offset + 1, offset + len(page)) if page else (0, 0)
    lines = [f"# db touchpoints: total={total} shown={first}-{last}"]
    lines += [f"{h.path}:{h.line}  {h.table}  {h.text}" for h in page]
    if offset + len(page) < total:
        lines.append(f"# TRUNCATED: {total - (offset + len(page))} more hits not shown. "
                     f"Re-run with --offset {offset + len(page)} to see them. The summary above is complete.")
    return "\n".join(lines)


def render_summary(summary: dict[str, dict]) -> str:
    modules = sorted({m for e in summary.values() for m in e["modules"]})
    lines = [f"# summary: {len(summary)} tables across modules {', '.join(modules)}"]
    lines += [f"{t}  count={e['count']}  modules={','.join(e['modules'])}" for t, e in summary.items()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args(argv)
    hits = scan(args.root)
    print(render_summary(summarize(hits)))
    print(render(hits, args.limit, args.offset))
    return 0


if __name__ == "__main__":
    sys.exit(main())
