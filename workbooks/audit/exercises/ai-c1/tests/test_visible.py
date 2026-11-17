"""Visible tests: one read tool, the test record and the approved write. Run: make test"""

from __future__ import annotations

from grcmcp.tokens import issue_approval

ENG = "ENG-2026-SOX-ITGC"
KEY = b"test-review-service-key-0f3a"
NOW = 1_793_000_000.0


def test_list_controls(mcp):
    err, data, _ = mcp.call("list_controls")
    assert not err and [c["control_id"] for c in data["controls"]] == ["CM-03", "AC-01", "AC-04", "OPS-02"]


def test_get_control_test(mcp):
    err, data, text = mcp.call("get_control_test", {"control_id": "CM-03"})
    assert not err, text
    assert data["sample_size"] == 25 and len(data["samples"]) == 25


def test_record_exception_with_approval(mcp, store):
    tok = issue_approval(KEY, engagement=ENG, control_id="CM-03", sample_id="CHG-104117", reviewer="kbrooks", expires_at=int(NOW) + 3600)
    err, data, text = mcp.call("record_exception", {"control_id": "CM-03", "sample_id": "CHG-104117",
                                                    "description": "approval recorded after the production deploy", "approval_token": tok})
    assert not err, text
    assert data["exception_id"].startswith("EXC-") and data["approved_by"] == "kbrooks"
    assert len(store.writes) == 1
