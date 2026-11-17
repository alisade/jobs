"""Human review gate for write actions on GRC Hub. The agent never calls this; the review UI does."""

from __future__ import annotations

from .store import GrcStore


class GateError(PermissionError):
    pass


def _check(store: GrcStore, exception_id: str, approval: dict | None, decision: str) -> dict:
    exc = store.exception(exception_id)
    if not approval:
        raise GateError(f"{exception_id}: a human approval record is required")
    if approval.get("exception_id") != exception_id:
        raise GateError(f"{exception_id}: approval is for {approval.get('exception_id')}")
    if approval.get("decision") != decision:
        raise GateError(f"{exception_id}: approval decision is {approval.get('decision')!r}, expected {decision!r}")
    reviewer = approval.get("reviewer")
    if reviewer not in store.reviewers:
        raise GateError(f"{exception_id}: {reviewer!r} is not an authorized reviewer")
    if reviewer == exc.get("prepared_by"):
        raise GateError(f"{exception_id}: reviewer is the preparer")
    if not str(approval.get("comment", "")).strip():
        raise GateError(f"{exception_id}: approval needs a comment")
    return exc


def close_exception(store: GrcStore, exception_id: str, approval: dict | None) -> None:
    exc = _check(store, exception_id, approval, "approve_close")
    if exc["status"] != "open":
        raise GateError(f"{exception_id} is {exc['status']}")
    store.set_status(exception_id, "closed", approval["reviewer"], approval["comment"], approval=dict(approval))
