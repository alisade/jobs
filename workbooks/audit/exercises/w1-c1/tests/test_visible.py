"""Visible tests: the happy path, one time-zone case and the basic contract. Run: make test"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from controlpilot.attributes import evaluate, overall
from controlpilot.contract import ChangeEvidence, DeployRecord
from controlpilot.extract import extract


def test_s01_happy_path(samples, tools, client_for, deploys, directory):
    client = client_for("S01")
    res = extract(client, samples["S01"], tools)
    assert res.status == "ok", res.errors
    assert res.tool_calls == ["get_ticket_approvals", "get_pr_checks"]
    assert res.usage.calls == 3
    results = evaluate(res.evidence, DeployRecord(**deploys["CHG-104118"]), directory)
    assert [r.result for r in results] == ["pass", "pass", "pass", "pass"]
    assert overall(results) == "pass"


def test_s06_approval_after_deploy_across_time_zones(samples, tools, client_for, deploys, directory):
    # approved 2026-06-03 09:30 +02:00 (07:30Z), deployed 08:00Z: that is BEFORE, so it passes.
    res = extract(client_for("S06"), samples["S06"], tools)
    assert res.status == "ok", res.errors
    results = evaluate(res.evidence, DeployRecord(**deploys["CHG-104455"]), directory)
    assert results[0].attribute == "approval_before_deploy"
    assert results[0].result == "pass"


def test_contract_rejects_missing_tests_passed():
    with pytest.raises(ValidationError):
        ChangeEvidence.model_validate({
            "change_id": "CHG-104118", "pr_number": 2231, "author": "dkwan", "approver": "lpatel",
            "approval_at": "2026-03-04T09:15:00-06:00",
            "citations": [{"source": "ticket", "locator": "approvals[0]", "quote": "approved"}],
        })
