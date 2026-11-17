"""Deterministic stand-ins for the evidence fetcher and the model-backed tester. Complete.

The real ControlPilot calls Gemini here; each call costs money and time, which is why a resumed run
must never repeat a step that was already committed. Calls are counted in CALLS.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

FIX = Path(__file__).resolve().parents[1] / "fixtures"
CALLS: Counter = Counter()


def sample_ids() -> list[str]:
    return sorted(json.loads((FIX / "samples.json").read_text()))


def fetch_evidence(sample_id: str) -> dict:
    CALLS[("evidence", sample_id)] += 1
    return json.loads((FIX / "samples.json").read_text())[sample_id]


def test_sample(sample_id: str, evidence: dict) -> dict:
    CALLS[("test", sample_id)] += 1
    attrs = {
        "approval_before_deploy": "pass" if evidence["approval_at"] < evidence["deployed_at"] else "exception",
        "independent_approver": "pass" if evidence["approver_id"] != evidence["author_id"] else "exception",
        "tests_passed": "pass" if evidence["ci"] == "success" else "exception",
    }
    outcome = "exception" if "exception" in attrs.values() else "pass"
    return {"outcome": outcome, "attributes": attrs, "model_version": "gemini-3.8-flash", "tokens": 2810}
