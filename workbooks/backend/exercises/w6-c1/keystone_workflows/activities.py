"""Activities for lead assignment. Side effects live here, never in workflow code.

Provided: you should not need to change this file. The accounts API and the notifier are fakes
with the behaviour of the real ones that matters here: the accounts API honours an
Idempotency-Key, and (like production last month) it can commit a write and then time out.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from temporalio import activity
from temporalio.exceptions import ApplicationError

from .models import REGION_MANAGERS, AssignInput, EscalationInput, Lead, ProposeInput


class FakeAccountsApi:
    """Stand-in for accounts-svc POST /v1/leads/{id}/assignment (Idempotency-Key aware)."""

    def __init__(self, fail_first_after_commit: bool = False) -> None:
        self.fail_first_after_commit = fail_first_after_commit
        self.calls = 0
        self.assignments: list[dict] = []
        self._by_key: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def assign(self, lead_id: str, tenant_id: str, owner_id: str, idempotency_key: str | None) -> str:
        self.calls += 1
        if idempotency_key and idempotency_key in self._by_key:
            return self._by_key[idempotency_key]["assignment_id"]
        row = {"assignment_id": f"asg-{next(self._ids):04d}", "lead_id": lead_id, "tenant_id": tenant_id,
               "owner_id": owner_id, "idempotency_key": idempotency_key}
        self.assignments.append(row)
        if idempotency_key:
            self._by_key[idempotency_key] = row
        if self.fail_first_after_commit and self.calls == 1:
            raise RuntimeError("accounts-svc: 504 upstream timeout (the write had already committed)")
        return row["assignment_id"]


@dataclass
class Notifier:
    sent: list[dict] = field(default_factory=list)

    def send(self, to: str, subject: str) -> None:
        self.sent.append({"to": to, "subject": subject})


class LeadActivities:
    """Activity implementations bound to their dependencies (register the bound methods)."""

    def __init__(self, api: FakeAccountsApi, notifier: Notifier) -> None:
        self.api = api
        self.notifier = notifier
        self.calls: dict[str, int] = {}

    def _count(self, name: str) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1

    @activity.defn
    async def score_lead(self, lead: Lead) -> int:
        self._count("score_lead")
        score = 20
        if lead.employees >= 1000:
            score += 50
        elif lead.employees >= 100:
            score += 25
        if not lead.email.endswith(("gmail.com", "outlook.com")):
            score += 15
        return min(score, 100)

    @activity.defn
    async def propose_owner(self, inp: ProposeInput) -> str:
        self._count("propose_owner")
        if inp.lead.region not in REGION_MANAGERS:
            # Retrying cannot fix bad input: fail the activity for good.
            raise ApplicationError(f"region {inp.lead.region!r} has no sales coverage", type="ValidationError", non_retryable=True)
        tier = "ent" if inp.score >= 70 else "mm"
        return f"usr-{inp.lead.region}-{tier}-rep-1"

    @activity.defn
    async def escalate(self, inp: EscalationInput) -> None:
        self._count("escalate")
        self.notifier.send(inp.to, f"Lead {inp.lead_id} ({inp.region}) waiting {inp.waited_hours} h for approval of {inp.proposed_owner}")

    @activity.defn
    async def assign_owner(self, inp: AssignInput) -> str:
        self._count("assign_owner")
        return self.api.assign(inp.lead_id, inp.tenant_id, inp.owner_id, inp.idempotency_key)

    def all(self) -> list:
        return [self.score_lead, self.propose_owner, self.escalate, self.assign_owner]
