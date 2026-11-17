from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidencekit.blobfake import FakeContainerClient  # noqa: E402

EMAIL = "CHG-104118/approval-email.layout.json"
CAB = "CAB/cab-minutes-2026-04-14.layout.json"
DEPLOY = "deploy-logs/prod-deploys-2026H1.csv"
OTHER = "CHG-104300/approval-email.layout.json"


@pytest.fixture
def container():
    return FakeContainerClient(ROOT / "evidence")


@pytest.fixture
def chunks(container):
    from evidencekit.chunks import build_chunks
    return build_chunks(container)


def claim_104118(**over):
    c = {"change_id": "CHG-104118", "conclusion": "approved_before_deploy",
         "approval_at": "2026-03-04T09:15:00-06:00", "deployed_at": "2026-03-04T16:20:00Z",
         "citations": [
             {"role": "approval", "blob": EMAIL, "page": 1, "paragraph": 5, "quote": "Approved. CHG-104118 may be deployed"},
             {"role": "approval", "blob": EMAIL, "page": 1, "paragraph": 3, "quote": "Date: 2026-03-04T09:15:00-06:00"},
             {"role": "deploy", "blob": DEPLOY, "row": 2, "quote": "CHG-104118,2231,prod,2026-03-04T16:20:00Z"}]}
    c.update(over)
    return c


def claim_104201(**over):
    c = {"change_id": "CHG-104201", "conclusion": "not_approved_before_deploy",
         "approval_at": "2026-04-14T15:30:00-05:00", "deployed_at": "2026-04-14T18:05:00Z",
         "citations": [
             {"role": "approval", "blob": CAB, "page": 2, "table": 0, "row": 2, "col": 2, "quote": "2026-04-14T15:30:00-05:00"},
             {"role": "deploy", "blob": DEPLOY, "row": 4, "col": 3, "quote": "2026-04-14T18:05:00Z"}]}
    c.update(over)
    return c
