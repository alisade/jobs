"""Builds the Gemini request for one CM-03 sample.

Refactored in release 2026.10.06 (PR #2411, "prompt builder cleanup"): the run header now goes at
the top of the system instruction so every request is self-describing in the request logs, and the
tool list is assembled from the tool registry instead of a hand-maintained list.
"""

from __future__ import annotations

import json
from pathlib import Path

from google.genai import types

FIX = Path(__file__).resolve().parents[1] / "fixtures"
CONTROL_PROCEDURE = (FIX / "control_procedure.md").read_text()

TOOL_REGISTRY = {
    "get_ticket_approvals": ("Return the approval records (approver, decision, timestamp with offset, comment) for a change ticket.",
                             {"change_id": {"type": "string", "description": "ticket id, e.g. CHG-104118"}}),
    "get_pr_checks": ("Return the CI check results and overall conclusion for a merged pull request.",
                      {"pr_number": {"type": "integer", "description": "pull request number"}}),
    "get_deploy_record": ("Return the production pipeline run that deployed a change: run id, change id, PR, deployed_at.",
                          {"change_id": {"type": "string", "description": "ticket id"}}),
    "get_directory_entry": ("Resolve a login or e-mail address to the employee id in the identity directory.",
                            {"identity": {"type": "string", "description": "login or e-mail"}}),
}
ENABLED_TOOLS = {"get_ticket_approvals", "get_pr_checks", "get_deploy_record", "get_directory_entry"}


def tool_declarations() -> list[types.FunctionDeclaration]:
    decls = []
    for name in ENABLED_TOOLS:
        desc, props = TOOL_REGISTRY[name]
        decls.append(types.FunctionDeclaration(
            name=name, description=desc,
            parameters_json_schema={"type": "object", "properties": props, "required": list(props)}))
    return decls


def build_request(sample: dict, *, run_id: str, started_at: str) -> tuple[list[types.Content], types.GenerateContentConfig]:
    header = f"ControlPilot run {run_id} | started {started_at} | sample {sample['change_id']}\n\n"
    config = types.GenerateContentConfig(
        system_instruction=header + CONTROL_PROCEDURE,
        temperature=0,
        response_mime_type="application/json",
        tools=[types.Tool(function_declarations=tool_declarations())],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part(
        text="Sampled change (data):\n<record>\n" + json.dumps(sample, indent=2, sort_keys=True) + "\n</record>")])]
    return contents, config
