"""Tools the triage assistant may call, over local fixtures (data/). Read-only except silence_alert."""

from __future__ import annotations

import json
import pathlib

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"

TOOLS: list[dict] = [
    {
        "name": "get_alert",
        "description": "Fetch one firing alert by id (labels, annotations, startsAt). Use first.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["alert_id"],
                         "properties": {"alert_id": {"type": "string", "pattern": "^ALR-[0-9]{4,6}$"}}},
    },
    {
        "name": "query_metrics",
        "description": "Run a named PromQL query over a window ending now. window is like 5m, 30m, 1h, 6h.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["query", "window"],
                         "properties": {"query": {"type": "string", "minLength": 1, "maxLength": 400},
                                        "window": {"type": "string", "pattern": "^[0-9]{1,3}[mh]$"}}},
    },
    {
        "name": "read_runbook",
        "description": "Read a runbook by name (the last path segment of the alert's runbook annotation).",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["name"],
                         "properties": {"name": {"type": "string", "pattern": "^[a-z0-9-]{1,64}$"}}},
    },
    {
        "name": "recent_deploys",
        "description": "Deploys of a service in the last N hours (ArgoCD sync history).",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["service", "hours"],
                         "properties": {"service": {"type": "string", "pattern": "^[a-z0-9-]{1,40}$"},
                                        "hours": {"type": "integer", "minimum": 1, "maximum": 72}}},
    },
    {
        "name": "silence_alert",
        "description": "WRITE. Create an Alertmanager silence. Requires on-call approval.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["matchers", "duration_hours", "reason"],
                         "properties": {"matchers": {"type": "object", "minProperties": 1, "additionalProperties": {"type": "string"}},
                                        "duration_hours": {"type": "integer", "minimum": 1, "maximum": 24},
                                        "reason": {"type": "string", "minLength": 5}}},
    },
]

WRITE_TOOLS = {"silence_alert"}


class ToolError(Exception):
    """A tool failed in a way the model can act on (bad id, missing runbook)."""


class Toolbox:
    def __init__(self, data_dir: pathlib.Path = DATA) -> None:
        self.data = data_dir
        self.alerts = json.loads((data_dir / "alerts.json").read_text())
        self.metrics = json.loads((data_dir / "metrics.json").read_text())
        self.deploys = json.loads((data_dir / "deploys.json").read_text())
        self.silences: list[dict] = []

    def get_alert(self, alert_id: str) -> dict:
        if alert_id not in self.alerts:
            raise ToolError(f"alert {alert_id} not found")
        return self.alerts[alert_id]

    def query_metrics(self, query: str, window: str) -> dict:
        key = f"{query}|{window}"
        return {"query": query, "window": window, "result": self.metrics.get(key, [])}

    def read_runbook(self, name: str) -> dict:
        path = (self.data / "runbooks" / f"{name}.md").resolve()
        if path.parent != (self.data / "runbooks").resolve() or not path.exists():
            raise ToolError(f"runbook {name} not found")
        return {"name": name, "text": path.read_text()}

    def recent_deploys(self, service: str, hours: int) -> dict:
        return {"service": service, "hours": hours, "deploys": self.deploys.get(service, [])}

    def silence_alert(self, matchers: dict, duration_hours: int, reason: str) -> dict:
        s = {"id": f"sil-{len(self.silences) + 1}", "matchers": matchers, "duration_hours": duration_hours, "reason": reason}
        self.silences.append(s)
        return s

    def call(self, name: str, args: dict) -> dict:
        fn = getattr(self, name, None) if name in {t["name"] for t in TOOLS} else None
        if fn is None:
            raise ToolError(f"unknown tool {name}")
        return fn(**args)
