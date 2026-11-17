"""CMS-0057-F decision clock.

expedited: 72 hours after receipt (elapsed time, so DST does not matter).
standard:  7 calendar days after receipt, on the wall clock of the plan's time zone (the local time of
           day is preserved across a DST change).
QHP issuers on the federally facilitated exchanges are outside these timeframes: no federal clock.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

NO_FEDERAL_CLOCK = {"qhp-ffe"}


def compute_deadline(received_at: datetime, priority: str, plan_type: str, plan_tz: str = "America/New_York") -> datetime | None:
    if received_at.tzinfo is None or received_at.utcoffset() is None:
        raise ValueError("received_at must be timezone-aware")
    if priority not in ("expedited", "standard"):
        raise ValueError(f"unknown priority {priority!r}")
    if plan_type in NO_FEDERAL_CLOCK:
        return None
    if priority == "expedited":
        return (received_at.astimezone(UTC) + timedelta(hours=72))
    local = received_at.astimezone(ZoneInfo(plan_tz))
    naive_due = local.replace(tzinfo=None) + timedelta(days=7)
    return naive_due.replace(tzinfo=ZoneInfo(plan_tz)).astimezone(UTC)
