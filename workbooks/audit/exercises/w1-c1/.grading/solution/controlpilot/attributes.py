"""Deterministic attribute evaluation for CM-03. No model calls here: the model extracts facts,
code decides whether each attribute passes."""

from __future__ import annotations

from typing import Literal

from .contract import AttributeResult, ChangeEvidence, DeployRecord, utc


def resolve(identity: str | None, directory: dict[str, str]) -> str | None:
    """Map an alias (login, e-mail) to an employee id; None when unknown."""
    if not identity:
        return None
    key = identity.strip().casefold()
    lowered = {k.casefold(): v for k, v in directory.items()}
    return lowered.get(key)


def evaluate(evidence: ChangeEvidence, deploy: DeployRecord, directory: dict[str, str]) -> list[AttributeResult]:
    out: list[AttributeResult] = []

    # A1 approval before deploy (compare instants, not wall-clock strings)
    if evidence.approver is None or evidence.approval_at is None:
        out.append(AttributeResult(attribute="approval_before_deploy", result="exception", detail="no approval evidence"))
    elif utc(evidence.approval_at) < utc(deploy.deployed_at):
        out.append(AttributeResult(attribute="approval_before_deploy", result="pass",
                                   detail=f"approved {utc(evidence.approval_at).isoformat()} before deploy {utc(deploy.deployed_at).isoformat()}"))
    else:
        out.append(AttributeResult(attribute="approval_before_deploy", result="exception",
                                   detail=f"approved {utc(evidence.approval_at).isoformat()}, not before deploy {utc(deploy.deployed_at).isoformat()}"))

    # A2 segregation of duties: approver is a different person than the author
    if evidence.approver is None:
        out.append(AttributeResult(attribute="independent_approver", result="exception", detail="no approver"))
    else:
        a, b = resolve(evidence.author, directory), resolve(evidence.approver, directory)
        if a is None or b is None:
            out.append(AttributeResult(attribute="independent_approver", result="not_evaluable",
                                       detail=f"identity not in directory: {evidence.author if a is None else evidence.approver}"))
        elif a == b:
            out.append(AttributeResult(attribute="independent_approver", result="exception",
                                       detail=f"author {evidence.author} and approver {evidence.approver} are the same person ({a})"))
        else:
            out.append(AttributeResult(attribute="independent_approver", result="pass", detail=f"{a} != {b}"))

    # A3 the deployed change is the ticketed change
    if deploy.change_id == evidence.change_id and deploy.pr_number == evidence.pr_number:
        out.append(AttributeResult(attribute="linked_change", result="pass", detail=f"{deploy.pipeline_run} deployed {deploy.change_id} / PR {deploy.pr_number}"))
    else:
        out.append(AttributeResult(attribute="linked_change", result="exception",
                                   detail=f"deploy {deploy.pipeline_run} is {deploy.change_id}/PR {deploy.pr_number}"))

    # A4 tests passed
    verdict: dict[bool | None, Literal["pass", "exception", "not_evaluable"]] = {True: "pass", False: "exception", None: "not_evaluable"}
    out.append(AttributeResult(attribute="tests_passed", result=verdict[evidence.tests_passed],
                               detail={True: "CI success", False: "CI failed", None: "no CI evidence"}[evidence.tests_passed]))
    return out


def overall(results: list[AttributeResult]) -> Literal["pass", "exception", "needs_review"]:
    if any(r.result == "exception" for r in results):
        return "exception"
    if any(r.result == "not_evaluable" for r in results):
        return "needs_review"
    return "pass"
