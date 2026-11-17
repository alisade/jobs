"""Helpers shared by the visible and hidden tests: load spec/inventory.json, validate its shape,
and resolve every evidence reference against the files under app/."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "spec" / "inventory.json"
SCHEMA = ROOT / "spec" / "inventory.schema.json"

SECTIONS = ["db_objects", "integrations", "auth_checks", "scheduled_jobs", "runtime_assumptions"]


def load() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf8"))


def items(inv: dict):
    for section in SECTIONS:
        for item in inv.get(section, []):
            yield section, item


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def resolve(ref: str, quote: str) -> str | None:
    """Return None when ref = 'app/...:<line>' exists and that line contains quote, else a reason."""
    m = re.fullmatch(r"(app/[^:]+):(\d+)", ref or "")
    if not m:
        return f"ref {ref!r} is not app/<path>:<line>"
    path = ROOT / m.group(1)
    if not path.is_file():
        return f"{ref}: no such file"
    lines = path.read_text(encoding="utf8", errors="replace").splitlines()
    n = int(m.group(2))
    if not 1 <= n <= len(lines):
        return f"{ref}: line out of range (file has {len(lines)} lines)"
    q = _norm(quote or "")
    if len(q) < 4:
        return f"{ref}: quote must be at least 4 characters"
    if q not in _norm(lines[n - 1]):
        return f"{ref}: quote {quote!r} not on that line (line is {lines[n - 1].strip()!r})"
    return None


def evidence_problems(inv: dict) -> list[str]:
    out = []
    for section, item in items(inv):
        ev = item.get("evidence") or []
        if not ev:
            out.append(f"{section}: {item.get('name') or item.get('role') or item.get('topic')}: no evidence")
        for e in ev:
            why = resolve(e.get("ref", ""), e.get("quote", ""))
            if why:
                out.append(f"{section}: {why}")
    return out


def files_of(item: dict) -> set[str]:
    return {e["ref"].rsplit(":", 1)[0].rsplit("/", 1)[-1] for e in item.get("evidence", []) if ":" in e.get("ref", "")}


def all_app_text() -> str:
    return "\n".join(p.read_text(encoding="utf8", errors="replace") for p in (ROOT / "app").rglob("*") if p.is_file()).upper()


def db_key(item: dict) -> str:
    name = item.get("name", "").upper().strip()
    if item.get("kind") == "procedure":
        return name.split("(")[0]
    name = name.split(".")[-1]
    return re.sub(r"_?[<{*\[].*$|_Y{2,4}$|_\d{4}$", "", name)
