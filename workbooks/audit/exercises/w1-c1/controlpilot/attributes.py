"""Deterministic attribute evaluation for CM-03. No model calls here: the model extracts facts,
code decides whether each attribute passes. See README task 3 for the rules."""

from __future__ import annotations

from typing import Literal

from .contract import AttributeResult, ChangeEvidence, DeployRecord, utc  # noqa: F401


def resolve(identity: str | None, directory: dict[str, str]) -> str | None:
    """Map an alias (login, e-mail) to an employee id; None when unknown. Complete."""
    if not identity:
        return None
    key = identity.strip().casefold()
    lowered = {k.casefold(): v for k, v in directory.items()}
    return lowered.get(key)


def evaluate(evidence: ChangeEvidence, deploy: DeployRecord, directory: dict[str, str]) -> list[AttributeResult]:
    """Return one AttributeResult per attribute, in this order:
    approval_before_deploy, independent_approver, linked_change, tests_passed."""
    raise NotImplementedError("TODO: README task 3")


def overall(results: list[AttributeResult]) -> Literal["pass", "exception", "needs_review"]:
    """exception if any attribute is an exception; needs_review if any is not_evaluable; else pass."""
    raise NotImplementedError("TODO: README task 3")
