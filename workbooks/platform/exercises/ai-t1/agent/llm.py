"""Deterministic stand-in for the model (no API key, no network).

The real model reads the terraform_plan tool output and reports a plan_summary. This fake does what the
recorded model did: it counts what it can see in the text it was given. If the tool output was cut
short, the model only sees the part that survived, exactly like a real model with a truncated tool
result. It never sees the plan file itself.
"""

from __future__ import annotations

import json
import re


class FakeModel:
    def summarize(self, system: str, tool_output: str) -> dict:
        try:
            data = json.loads(tool_output)
        except ValueError:
            data = None
        if isinstance(data, dict) and "counts" in data:  # a compact summary from the tool
            c = data["counts"]
            return {"to_import": c.get("import", 0), "to_add": c.get("add", 0),
                    "to_change": c.get("change", 0), "to_destroy": c.get("destroy", 0)}
        text = tool_output
        return {
            "to_import": len(re.findall(r'"importing"', text)),
            "to_add": len(re.findall(r'"actions":\s*\[\s*"create"', text)),
            "to_change": len(re.findall(r'"actions":\s*\[\s*"update"', text)),
            "to_destroy": len(re.findall(r'"actions":\s*\[\s*"delete"', text)),
        }
