"""Post-render guard: fail the release if a rendered definition still points at another environment.

Usage: uv run python deploy/check_bindings.py --env PROD --rendered DIR [--targets deploy/targets.json]
Exit code 1 and one line per leak when any GUID owned by a different environment remains.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def guid_owners(targets: dict) -> dict[str, tuple[str, str]]:
    """guid (lowercase) -> (env, label) for every workspace and item in targets.json."""
    owners: dict[str, tuple[str, str]] = {}
    for env, t in targets.items():
        if env.startswith("_"):
            continue
        owners[t["workspace_id"].lower()] = (env, f"workspace {t['workspace_name']}")
        for itype, items in t.get("items", {}).items():
            for name, gid in items.items():
                owners[gid.lower()] = (env, f"{itype} {name}")
    return owners


def find_leaks(rendered: Path, env: str, targets: dict) -> list[str]:
    """Return 'relpath: guid (ENV label)' for every foreign-environment GUID in rendered item files."""
    if env not in targets:
        raise ValueError(f"unknown environment {env!r}")
    owners = guid_owners(targets)
    leaks: list[str] = []
    for f in sorted(Path(rendered).rglob("*")):
        if not f.is_file() or f.name == ".platform":
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        rel = f.relative_to(rendered).as_posix()
        for g in sorted({m.lower() for m in GUID.findall(text)}):
            owner = owners.get(g)
            if owner and owner[0] != env:
                leaks.append(f"{rel}: {g} ({owner[0]} {owner[1]})")
    return leaks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--rendered", required=True)
    ap.add_argument("--targets", default="deploy/targets.json")
    a = ap.parse_args()
    leaks = find_leaks(Path(a.rendered), a.env, json.loads(Path(a.targets).read_text()))
    for leak in leaks:
        print(f"LEAK {leak}")
    print(f"{len(leaks)} cross-environment reference(s) in {a.rendered} for {a.env}")
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main())
