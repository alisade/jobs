"""Read-only lookups over the exported change and CI systems (fixtures/). Complete."""

from __future__ import annotations

import json
from pathlib import Path

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIX / name).read_text())


def samples() -> dict:
    return _load("samples.json")


def deploys() -> dict:
    return _load("deploys.json")


def directory() -> dict:
    return _load("directory.json")


def tools() -> dict:
    sysdata = _load("systems.json")

    def get_ticket_approvals(change_id: str) -> list[dict]:
        if change_id not in sysdata["approvals"]:
            raise KeyError(f"unknown change ticket {change_id}")
        return sysdata["approvals"][change_id]

    def get_pr_checks(pr_number: int) -> dict:
        key = str(int(pr_number))
        if key not in sysdata["checks"]:
            raise KeyError(f"unknown pull request {pr_number}")
        return sysdata["checks"][key]

    return {"get_ticket_approvals": get_ticket_approvals, "get_pr_checks": get_pr_checks}
