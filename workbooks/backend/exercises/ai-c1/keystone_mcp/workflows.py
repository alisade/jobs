"""Fake client for keystone-workflows (Temporal in production). Provided; do not change.

start_approval starts an approval workflow and returns its proposal id. Like Temporal with a fixed
workflow id, starting twice with the same idempotency key returns the same proposal.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FakeWorkflowClient:
    started: list[dict] = field(default_factory=list)
    _by_key: dict[str, str] = field(default_factory=dict)

    def start_approval(self, kind: str, payload: dict, *, idempotency_key: str, on_behalf_of: str, agent_id: str) -> str:
        if idempotency_key in self._by_key:
            return self._by_key[idempotency_key]
        pid = f"prop-{len(self._by_key) + 1:04d}"
        self._by_key[idempotency_key] = pid
        self.started.append({"proposal_id": pid, "kind": kind, "payload": payload,
                             "on_behalf_of": on_behalf_of, "agent_id": agent_id})
        return pid
