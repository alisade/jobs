"""CMS-0057-F decision clock. TODO: make it correct (see README, "Decision clock")."""

from __future__ import annotations

from datetime import datetime, timedelta


def compute_deadline(received_at: datetime, priority: str, plan_type: str, plan_tz: str = "America/New_York") -> datetime | None:
    # Naive first draft: ignores time zones, DST and plan types.
    days = 3 if priority == "expedited" else 7
    return received_at + timedelta(days=days)
