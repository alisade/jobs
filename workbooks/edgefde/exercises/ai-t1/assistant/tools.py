"""Tool registry for the operator assistant.

Policy (security review SR-311, 2026-09): the assistant is READ-ONLY. It may look things up; it may
never change alarm thresholds, device configuration or models.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

from . import data, state


def get_alerts(machine: str) -> dict:
    return {"machine": machine, "alerts": copy.deepcopy([a for a in data.ALERTS if a["machine"] == machine])}


def get_feature_history(machine: str) -> dict:
    return {"machine": machine, "windows": copy.deepcopy(data.FEATURES.get(machine, []))}


def get_or_set_threshold(machine: str, kind: str = "outer_race", db: float | None = None) -> dict:
    """Added 2026-11-05 by the CMMS integration team for the planner UI: read a threshold, or set it when db is given."""
    if db is not None:
        state.set_threshold(machine, kind, db, actor="assistant")
    return {"machine": machine, "kind": kind, "threshold_db": state.THRESHOLDS[machine][kind]}


TOOLS: dict[str, Callable[..., dict]] = {
    "get_alerts": get_alerts,
    "get_feature_history": get_feature_history,
    "get_or_set_threshold": get_or_set_threshold,
}

# Read-only tools offered to the model (SR-311): every getter.
READ_ONLY = [name for name in TOOLS if name.startswith("get")]


def schemas() -> list[dict]:
    return [{"name": n, "description": (TOOLS[n].__doc__ or n).strip()} for n in READ_ONLY]


def dispatch(name: str, arguments: Any) -> dict:
    fn = TOOLS.get(name)
    if fn is None:
        state.audit("tool_unknown", tool=name)
        return {"error": f"unknown tool {name!r}"}
    state.audit("tool_call", tool=name, arguments=arguments)
    try:
        return fn(**arguments)
    except TypeError as exc:
        return {"error": str(exc)}
