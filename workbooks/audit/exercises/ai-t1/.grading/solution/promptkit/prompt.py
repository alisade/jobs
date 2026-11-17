"""Builds the Gemini request for one CM-03 sample.

Cache-friendly order: everything that is identical for every request comes first and is
byte-stable (tool declarations in a fixed order, a static system instruction); everything that
varies per request (the sample, the run) comes last, in the user content. The run header is
request metadata for logs, not prompt text.
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
# An ordered tuple, not a set: set iteration order of str depends on PYTHONHASHSEED, which differs per process.
ENABLED_TOOLS = ("get_deploy_record", "get_directory_entry", "get_pr_checks", "get_ticket_approvals")


def tool_declarations() -> list[types.FunctionDeclaration]:
    decls = []
    for name in sorted(ENABLED_TOOLS):
        desc, props = TOOL_REGISTRY[name]
        decls.append(types.FunctionDeclaration(
            name=name, description=desc,
            parameters_json_schema={"type": "object", "properties": props, "required": list(props)}))
    return decls


SYSTEM_INSTRUCTION = CONTROL_PROCEDURE  # static: no run id, no timestamp, no sample id


def build_request(sample: dict, *, run_id: str, started_at: str) -> tuple[list[types.Content], types.GenerateContentConfig]:
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0,
        response_mime_type="application/json",
        tools=[types.Tool(function_declarations=tool_declarations())],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    # run_id / started_at belong in the execution log and request labels, not in the prompt.
    contents = [types.Content(role="user", parts=[types.Part(
        text="Sampled change (data):\n<record>\n" + json.dumps(sample, indent=2, sort_keys=True) + "\n</record>")])]
    return contents, config
