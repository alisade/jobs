"""Visible tests: what the DLP scanner flagged must not reach the log."""

from __future__ import annotations

from x2_support import pii_findings

from trustlog.core import log_started
from trustlog.decisions import DecisionEvent, log_decision
from trustlog.risk_client import log_risk_failure


def _event(**kw):
    base = dict(
        decision_id="dec-1", hook="checkout", outcome="deny", reason_codes=["velocity_high"],
        amount=120.5, card_bin="411111", customer_email="maria.lopez@example.com",
    )
    return DecisionEvent(**(base | kw))


def test_lifecycle_lines_on_the_parent_logger_are_redacted(capture):
    log_started("northwind-prod", "oncall@northwind.example")
    assert pii_findings(capture.raw()) == []


def test_decision_lines_carry_no_email_or_card_bin(capture):
    log_decision(_event())
    raw = capture.raw()
    assert pii_findings(raw) == [], raw


def test_risk_failures_carry_no_card_number(capture):
    log_risk_failure("j.chen@example.org", "4111 1111 1111 1111", "ReadTimeout")
    raw = capture.raw()
    assert pii_findings(raw) == [], raw
