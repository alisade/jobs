"""Durable CM-03 test run with a human review gate.

Per sample:  evidence -> test -> [review if exception] -> workpaper -> grc_issue (confirmed exceptions only)

Every step output is committed to the CheckpointStore; a committed step is never executed again.
Side effects (workpaper blob, GRC issue) are idempotent: deterministic blob names with
overwrite=False plus a compare on conflict, and a GRC Idempotency-Key derived from
(run_id, sample_id, step) that is identical on every attempt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .fakes import CrashInjected, ResourceExistsError
from .log import ExecutionLog
from .store import CheckpointStore

STEPS = ("evidence", "test", "review", "workpaper", "grc_issue")


class ReviewError(ValueError):
    """A review request that violates the review rules."""


def idempotency_key(run_id: str, sample_id: str, step: str) -> str:
    return f"{run_id}/{sample_id}/{step}"


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

    # ---------------- helpers ----------------
    def _crash(self, sample_id: str, step: str, when: str) -> None:
        if self.crash_at == (sample_id, step, when):
            self.crash_at = None
            raise CrashInjected(f"injected crash {when} {step} for {sample_id}")

    def _commit(self, sample_id: str, step: str, output: Any, state: str) -> None:
        self.store.put_step(self.run_id, sample_id, step, output, state=state)
        self.log.append("step_completed", run_id=self.run_id, sample_id=sample_id, step=step, output=output)

    def status(self, sample_id: str) -> str | None:
        return self.store.state(self.run_id, sample_id)

    def pending_reviews(self) -> list[str]:
        return [s for s, st in self.store.samples(self.run_id) if st == "awaiting_review"]

    # ---------------- run ----------------
    def run(self) -> dict:
        for sample_id, _ in self.store.samples(self.run_id):
            self._advance(sample_id)
        states = dict(self.store.samples(self.run_id))
        return {
            "done": sorted(s for s, st in states.items() if st == "done"),
            "awaiting_review": sorted(s for s, st in states.items() if st == "awaiting_review"),
        }

    def _advance(self, sid: str) -> None:
        get = lambda step: self.store.get_step(self.run_id, sid, step)  # noqa: E731
        if self.status(sid) in ("done", "awaiting_review"):
            return

        evidence = get("evidence")
        if evidence is None:
            self._crash(sid, "evidence", "before")
            evidence = self.evidence_fn(sid)
            self._crash(sid, "evidence", "after")
            self._commit(sid, "evidence", evidence, "evidenced")

        result = get("test")
        if result is None:
            self._crash(sid, "test", "before")
            result = self.test_fn(sid, evidence)
            self._crash(sid, "test", "after")
            if result["outcome"] == "exception":
                self._commit(sid, "test", result, "awaiting_review")
                self.log.append("review_requested", run_id=self.run_id, sample_id=sid, attributes=result["attributes"])
                return
            self._commit(sid, "test", result, "tested")

        review = get("review")
        if result["outcome"] == "exception" and review is None:
            self.store.set_state(self.run_id, sid, "awaiting_review")
            return
        conclusion = review["conclusion"] if review else result["outcome"]

        if get("workpaper") is None:
            row = {
                "run_id": self.run_id, "sample_id": sid, "control": "CM-03",
                "attributes": result["attributes"], "model_conclusion": result["outcome"],
                "conclusion": conclusion, "preparer": self.preparer, "review": review,
                "evidence": evidence,
            }
            data = json.dumps(row, sort_keys=True, indent=2)
            name = workpaper_blob_name(self.run_id, sid)
            self._crash(sid, "workpaper", "before")
            try:
                self.blob.upload_blob(name, data, overwrite=False)
            except ResourceExistsError:
                existing = self.blob.download_blob(name).readall().decode()
                if existing != data:
                    raise RuntimeError(f"workpaper {name} exists with different content")
            self._crash(sid, "workpaper", "after")
            self._commit(sid, "workpaper", {"blob": name}, "published")

        if conclusion == "exception" and get("grc_issue") is None:
            key = idempotency_key(self.run_id, sid, "grc_issue")
            payload = {"control": "CM-03", "sample_id": sid, "run_id": self.run_id,
                       "attributes": result["attributes"], "review": review}
            self.log.append("side_effect_intent", run_id=self.run_id, sample_id=sid, step="grc_issue", key=key)
            self._crash(sid, "grc_issue", "before")
            resp = self.grc.create_issue(payload, idempotency_key=key)
            self._crash(sid, "grc_issue", "after")
            self._commit(sid, "grc_issue", {"issue_id": resp["issue_id"], "key": key}, "done")
        else:
            self.store.set_state(self.run_id, sid, "done")
            self.log.append("sample_done", run_id=self.run_id, sample_id=sid, conclusion=conclusion)

    # ---------------- review gate ----------------
    def review(self, sample_id: str, *, reviewer: str, decision: str,
               reason: str | None = None, evidence_ref: str | None = None) -> dict:
        if self.status(sample_id) != "awaiting_review":
            raise ReviewError(f"{sample_id} is not awaiting review (state {self.status(sample_id)})")
        if not reviewer or reviewer.strip().casefold() == self.preparer.strip().casefold():
            raise ReviewError("reviewer must be a different person than the preparer")
        if decision not in ("confirm", "override"):
            raise ReviewError("decision must be 'confirm' or 'override'")
        if decision == "override" and (not reason or not reason.strip() or not evidence_ref or not evidence_ref.strip()):
            raise ReviewError("an override needs a reason and an evidence reference")
        rec = {"reviewer": reviewer, "decision": decision, "reason": reason, "evidence_ref": evidence_ref,
               "conclusion": "exception" if decision == "confirm" else "pass"}
        self.store.put_step(self.run_id, sample_id, "review", rec, state="reviewed")
        self.log.append("review", run_id=self.run_id, sample_id=sample_id, **rec)
        return rec
