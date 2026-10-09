"""Post-render guard: fail the release if a rendered definition still points at another environment.

Usage: uv run python deploy/check_bindings.py --env PROD --rendered DIR [--targets deploy/targets.json]
Exit code 1 and one line per leak when any GUID owned by a different environment remains.

TODO (part of the fix): implement find_leaks() and main(). Contract in README, section "Guard".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def find_leaks(rendered: Path, env: str, targets: dict) -> list[str]:
    """Return 'relpath: guid (ENV label)' for every foreign-environment GUID in rendered item files."""
    # TODO
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--rendered", required=True)
    ap.add_argument("--targets", default="deploy/targets.json")
    a = ap.parse_args()
    leaks = find_leaks(Path(a.rendered), a.env, json.loads(Path(a.targets).read_text()))
    for leak in leaks:
        print(f"LEAK {leak}")
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main())
