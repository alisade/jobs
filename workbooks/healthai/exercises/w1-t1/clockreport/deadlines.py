"""Decision deadlines for prior authorization requests (CMS-0057-F impacted lines of business).

History: moved here from the legacy UM toolkit in release 2026.09 so the metrics report and the
reviewer queue share one implementation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

log = logging.getLogger("clockreport.deadlines")

EXPEDITED_HOURS = 72
STANDARD_DAYS = 7  # UM-POL-12: "decision within 7 days of receipt of the request"


def add_days(start: datetime, days: int, business: bool = True) -> datetime:
    """Add days to a naive local datetime. Business days skip Saturday and Sunday (legacy toolkit API)."""
    if not business:
        return start + timedelta(days=days)
    out, added = start, 0
    while added < days:
        out += timedelta(days=1)
        if out.weekday() < 5:
            added += 1
    return out


def decision_deadline(received_at: datetime, priority: str, plan_tz: str, case_id: str = "") -> datetime:
    """Return the decision deadline as an aware UTC datetime."""
    if received_at.tzinfo is None:
        raise ValueError("received_at must be timezone-aware")
    if priority == "expedited":
        return received_at.astimezone(UTC) + timedelta(hours=EXPEDITED_HOURS)
    if priority != "standard":
        raise ValueError(f"unknown priority {priority!r}")
    zone = ZoneInfo(plan_tz)
    local = received_at.astimezone(zone)
    due_local = add_days(local.replace(tzinfo=None), STANDARD_DAYS).replace(tzinfo=zone)
    if due_local.utcoffset() != local.utcoffset():
        log.warning("case %s: UTC offset changes between receipt and due date (DST); local time of day preserved", case_id)
    return due_local.astimezone(UTC)
