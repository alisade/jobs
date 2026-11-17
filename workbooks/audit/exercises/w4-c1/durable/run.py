"""Durable CM-03 test run with a human review gate. TODO: README tasks 1, 2 and 4.

Per sample:  evidence -> test -> [review if exception] -> workpaper -> grc_issue (confirmed exceptions only)

Sample states: pending -> evidenced -> tested | awaiting_review -> reviewed -> published -> done
(a sample with no GRC issue to raise goes from published straight to done).
"""

from __future__ import annotations

import json  # noqa: F401
from pathlib import Path
from typing import Any, Callable

from .fakes import CrashInjected, ResourceExistsError  # noqa: F401
from .log import ExecutionLog
from .store import CheckpointStore

STEPS = ("evidence", "test", "review", "workpaper", "grc_issue")


class ReviewError(ValueError):
    """A review request that violates the review rules."""


def idempotency_key(run_id: str, sample_id: str, step: str) -> str:
    """The GRC Idempotency-Key for a step: f"{run_id}/{sample_id}/{step}", identical on every attempt."""
    raise NotImplementedError("TODO: README task 2")


def workpaper_blob_name(run_id: str, sample_id: str) -> str:
    return f"{run_id}/workpaper/{sample_id}.json"


class TestRun:
    __test__ = False  # not a pytest test class

    def __init__(
        self,
        run_id: str,
        samples: list[str],
        *,
        db_path: str | Path,
        log_path: str | Path,
        preparer: str,
        evidence_fn: Callable[[str], dict],
        test_fn: Callable[[str, dict], dict],
        blob: Any,
        grc: Any,
        crash_at: tuple[str, str, str] | None = None,
    ):
        self.run_id = run_id
        self.preparer = preparer
        self.evidence_fn, self.test_fn = evidence_fn, test_fn
        self.blob, self.grc = blob, grc
        self.crash_at = crash_at
        self.store = CheckpointStore(db_path)
        self.log = ExecutionLog(log_path)
        resumed = bool(self.store.samples(run_id))
        for s in samples:
            self.store.add_sample(run_id, s)
        self.log.append("run_resumed" if resumed else "run_started", run_id=run_id, preparer=preparer, samples=sorted(samples))

    def _crash(self, sample_id: str, step: str, when: str) -> None:
        """Crash-injection hook. Call _crash(sid, step, "before") right before a step's work and
        _crash(sid, step, "after") right after the work (side effect done) but BEFORE you commit it."""
        if self.crash_at == (sample_id, step, when):
            self.crash_at = None
            raise CrashInjected(f"injected crash {when} {step} for {sample_id}")

    def status(self, sample_id: str) -> str | None:
        return self.store.state(self.run_id, sample_id)

    def pending_reviews(self) -> list[str]:
        return [s for s, st in self.store.samples(self.run_id) if st == "awaiting_review"]

    def run(self) -> dict:
        """Advance every sample as far as it can go. Return
        {"done": [sample ids], "awaiting_review": [sample ids]} (both sorted)."""
        raise NotImplementedError("TODO: README task 1")

    def review(self, sample_id: str, *, reviewer: str, decision: str,
               reason: str | None = None, evidence_ref: str | None = None) -> dict:
        """Record a reviewer decision ("confirm" or "override") for a sample awaiting review."""
        raise NotImplementedError("TODO: README task 4")
