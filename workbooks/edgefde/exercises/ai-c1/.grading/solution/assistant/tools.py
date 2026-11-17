"""Read-only tools over the pipeline data. Every tool returns a JSON-serialisable dict; failures are
returned as {"error": "..."} so the model can recover, never raised into the loop."""

from __future__ import annotations

import copy
from typing import Any, Callable

from . import data

LOCAL_ONLY = {"get_raw_capture"}


def get_alerts(machine: str, since: str | None = None) -> dict:
    if machine not in data.FEATURES:
        return {"error": f"unknown machine {machine!r}; known: {sorted(data.FEATURES)}"}
    rows = [a for a in data.ALERTS if a["machine"] == machine and (since is None or a["ts"] >= since)]
    return {"machine": machine, "alerts": copy.deepcopy(rows)}


def get_feature_history(machine: str, start: str, end: str) -> dict:
    if machine not in data.FEATURES:
        return {"error": f"unknown machine {machine!r}; known: {sorted(data.FEATURES)}"}
    if start > end:
        return {"error": "start must be <= end"}
    rows = [r for r in data.FEATURES[machine] if start <= r["window_start"] <= end]
    return {"machine": machine, "windows": copy.deepcopy(rows)}


def get_model_card() -> dict:
    return copy.deepcopy(data.MODEL_CARD)


def get_raw_capture(machine: str) -> dict:
    if machine not in data.RAW_CAPTURES:
        return {"error": f"no raw capture for {machine!r}"}
    return copy.deepcopy(data.RAW_CAPTURES[machine])


TOOLS: dict[str, Callable[..., dict]] = {
    "get_alerts": get_alerts,
    "get_feature_history": get_feature_history,
    "get_model_card": get_model_card,
    "get_raw_capture": get_raw_capture,
}

SCHEMAS: list[dict] = [
    {"name": "get_alerts", "description": "Alerts for one machine (for example P04), newest last. Optional ISO-8601 'since'.",
     "parameters": {"type": "object", "properties": {"machine": {"type": "string"}, "since": {"type": "string"}}, "required": ["machine"]}},
    {"name": "get_feature_history", "description": "Hourly feature windows (rms, kurtosis, bpfo_db) for a machine between two ISO-8601 times.",
     "parameters": {"type": "object", "properties": {"machine": {"type": "string"}, "start": {"type": "string"}, "end": {"type": "string"}}, "required": ["machine", "start", "end"]}},
    {"name": "get_model_card", "description": "The deployed model's card: version, training data, holdout metrics, limitations.",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "get_raw_capture", "description": "Raw waveform samples for a machine (stays on site).",
     "parameters": {"type": "object", "properties": {"machine": {"type": "string"}}, "required": ["machine"]}},
]


def schemas(include_local_only: bool = True) -> list[dict]:
    return [s for s in SCHEMAS if include_local_only or s["name"] not in LOCAL_ONLY]


def dispatch(name: str, arguments: Any, allowed: set[str] | None = None) -> dict:
    allowed = set(TOOLS) if allowed is None else allowed
    if name not in TOOLS or name not in allowed:
        return {"error": f"unknown tool {name!r}; available: {sorted(allowed & set(TOOLS))}"}
    if not isinstance(arguments, dict):
        return {"error": "arguments must be a JSON object"}
    try:
        return TOOLS[name](**arguments)
    except TypeError as exc:
        return {"error": f"bad arguments for {name}: {exc}"}
