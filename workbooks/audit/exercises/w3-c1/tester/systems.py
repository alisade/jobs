"""Mock change, source-control and deploy systems plus the shared tool registry. Complete; do not edit.

TOOL_REGISTRY is shared by every ControlPilot skill. It contains write tools used by other skills
(close_change is the change-management team's remediation skill). EXECUTED records every tool body
that actually ran, so tests can prove a call was blocked rather than merely ignored.
"""

from __future__ import annotations

from google.adk.tools import ToolContext

EXECUTED: list[tuple[str, dict]] = []

TICKETS = {
    "CHG-104118": {"id": "CHG-104118", "author": "dkwan", "approvals": [{"approver": "lpatel", "at": "2026-03-04T09:15:00-06:00"}], "pr_number": 2231},
    "CHG-104163": {"id": "CHG-104163", "author": "mreyes", "approvals": [{"approver": "tnguyen", "at": "2026-03-11T10:05:00-05:00"}], "pr_number": 2240},
    "CHG-104390": {"id": "CHG-104390", "author": "j.ortiz", "approvals": [{"approver": "jortiz@meridianfreight.example", "at": "2026-05-20T08:01:00-05:00"}], "pr_number": 2302},
    "CHG-104999": {"id": "CHG-104999", "author": "cfo-office", "approvals": [], "pr_number": 2399, "note": "board-confidential acquisition change"},
}
PRS = {
    2231: {"number": 2231, "author": "dkwan", "checks": "success"},
    2240: {"number": 2240, "author": "mreyes", "checks": "success"},
    2302: {"number": 2302, "author": "j.ortiz", "checks": "success"},
    2399: {"number": 2399, "author": "cfo-office", "checks": "success"},
}
DEPLOYS = {
    "CHG-104118": {"change_id": "CHG-104118", "deployed_at": "2026-03-04T16:20:00Z"},
    "CHG-104163": {"change_id": "CHG-104163", "deployed_at": "2026-03-11T21:00:00Z"},
    "CHG-104390": {"change_id": "CHG-104390", "deployed_at": "2026-05-20T14:00:00Z"},
    "CHG-104999": {"change_id": "CHG-104999", "deployed_at": "2026-05-29T03:00:00Z"},
}


def list_sample(tool_context: ToolContext) -> dict:
    """List the change ids in the current CM-03 sample. Call this first."""
    EXECUTED.append(("list_sample", {}))
    return {"sample": list(tool_context.state.get("sample_ids", []))}


def get_ticket(change_id: str) -> dict:
    """Fetch a change ticket (author, approvals with timestamps, linked PR number) by id, e.g. CHG-104118."""
    EXECUTED.append(("get_ticket", {"change_id": change_id}))
    if change_id not in TICKETS:
        return {"error": f"no ticket {change_id}"}
    return TICKETS[change_id]


def get_pr(pr_number: int) -> dict:
    """Fetch a merged pull request (author, CI check conclusion) by number."""
    EXECUTED.append(("get_pr", {"pr_number": pr_number}))
    pr = PRS.get(int(pr_number))
    return pr if pr else {"error": f"no PR {pr_number}"}


def get_deploy_record(change_id: str) -> dict:
    """Fetch the production deploy record (deployed_at in UTC) for a change id."""
    EXECUTED.append(("get_deploy_record", {"change_id": change_id}))
    return DEPLOYS.get(change_id, {"error": f"no deploy for {change_id}"})


def record_result(change_id: str, result: str, failed_attributes: list[str], citations: list[str], tool_context: ToolContext) -> dict:
    """Record the test result for one sampled change. result is pass, exception or needs_review;
    failed_attributes lists the CM-03 attributes that failed; citations name the records used."""
    EXECUTED.append(("record_result", {"change_id": change_id, "result": result}))
    results = dict(tool_context.state.get("results", {}))
    results[change_id] = {"result": result, "failed_attributes": list(failed_attributes), "citations": list(citations)}
    tool_context.state["results"] = results
    return {"recorded": change_id}


def close_change(change_id: str, resolution: str) -> dict:
    """Close a change ticket in the change system (remediation skill only)."""
    EXECUTED.append(("close_change", {"change_id": change_id}))
    return {"closed": change_id}


TOOL_REGISTRY = {f.__name__: f for f in (list_sample, get_ticket, get_pr, get_deploy_record, record_result, close_change)}
READ_TOOLS = ("list_sample", "get_ticket", "get_pr", "get_deploy_record")
