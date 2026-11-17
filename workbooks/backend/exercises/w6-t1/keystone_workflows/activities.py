"""Activities (side effects). Unchanged in this release except for the new enrich_lead."""

from __future__ import annotations

from temporalio import activity

from .models import AssignInput, EscalationInput, Lead, ProposeInput


class LeadActivities:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}
        self.assigned: list[AssignInput] = []

    def _count(self, name: str) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1

    @activity.defn
    async def score_lead(self, lead: Lead) -> int:
        self._count("score_lead")
        return 85 if lead.employees >= 1000 else 45

    @activity.defn
    async def enrich_lead(self, lead: Lead) -> dict:
        """New in 2026.45: firmographics from the enrichment vendor (cached)."""
        self._count("enrich_lead")
        return {"industry": "logistics", "hq_country": "NO", "employees_band": "1000-5000"}

    @activity.defn
    async def propose_owner(self, inp: ProposeInput) -> str:
        self._count("propose_owner")
        tier = "ent" if inp.score >= 70 else "mm"
        return f"usr-{inp.lead.region}-{tier}-rep-1"

    @activity.defn
    async def escalate(self, inp: EscalationInput) -> None:
        self._count("escalate")

    @activity.defn
    async def assign_owner(self, inp: AssignInput) -> str:
        self._count("assign_owner")
        self.assigned.append(inp)
        return f"asg-{inp.lead_id}"

    def all(self) -> list:
        return [self.score_lead, self.enrich_lead, self.propose_owner, self.escalate, self.assign_owner]
