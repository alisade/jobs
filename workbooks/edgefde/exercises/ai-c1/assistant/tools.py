"""Read-only tools over the pipeline data. TODO: implement the four tools, schemas() and dispatch().

Every tool returns a JSON-serialisable dict; failures are
returned as {"error": "..."} so the model can recover, never raised into the loop."""

from __future__ import annotations

import copy
from typing import Any, Callable

from . import data

LOCAL_ONLY = {"get_raw_capture"}


def get_alerts(machine: str, since: str | None = None) -> dict:
    """{"machine", "alerts": [...]} for one machine, optionally only alerts with ts >= since."""
    raise NotImplementedError("TODO")


def get_feature_history(machine: str, start: str, end: str) -> dict:
    """{"machine", "windows": [...]} with start <= window_start <= end."""
    raise NotImplementedError("TODO")


def get_model_card() -> dict:
    raise NotImplementedError("TODO")


def get_raw_capture(machine: str) -> dict:
    raise NotImplementedError("TODO")


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
    """Tool schemas to offer the model; without the LOCAL_ONLY tools when include_local_only is False."""
    raise NotImplementedError("TODO")


def dispatch(name: str, arguments: Any, allowed: set[str] | None = None) -> dict:
    """Run one tool call. Unknown or not-allowed tools and bad arguments return {"error": ...}."""
    raise NotImplementedError("TODO")
