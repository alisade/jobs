"""Context for one run of a scheduled report job. Built by the scheduler from the job definition
that a tenant admin created and approved in the Tidewater console; never from model output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class JobContext:
    tenant_id: str
    run_id: str
    run_date: str                                   # YYYY-MM-DD
    approved_recipients: tuple[str, ...] = field(default_factory=tuple)   # from the approved job definition
    task: str = ""
