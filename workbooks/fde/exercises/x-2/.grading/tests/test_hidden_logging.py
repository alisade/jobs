"""Hidden tests for fde/x-2: redaction holds for every trust.* logger, structure survives."""

from __future__ import annotations

import logging

import pytest
from x2_hidden_support import pii_findings

from trustlog.decisions import DecisionEvent, log_decision
from trustlog.redact import RedactingFilter
from trustlog.risk_client import log_risk_failure

EMAIL = "maria.lopez@example.com"


def _event(**kw):
    base = dict(
        decision_id="dec-77", hook="checkout", outcome="review", reason_codes=["device_mismatch"],
        amount=88.25, card_bin="37828200", customer_email=EMAIL,
    )
    return DecisionEvent(**(base | kw))


@pytest.mark.parametrize(
    "name", ["trust", "trust.decisions", "trust.risk", "trust.outcomes.chargebacks", "trust.a.b.c.d"]
)
def test_any_trust_logger_at_any_depth_is_redacted(capture, name):
    logging.getLogger(name).warning(
        "lookup for %s with card 5555-4444-3333-2222", EMAIL, extra={"customer": {"email": EMAIL}}
    )
    raw = capture.raw()
    assert raw.strip(), "the record must still be written"
    assert pii_findings(raw) == [], raw


def test_child_logger_created_after_configure_is_redacted(capture):
    late = logging.getLogger("trust.outcomes.refunds.v2")  # a module added next sprint
    late.setLevel(logging.DEBUG)
    late.info("refund for %s", EMAIL)
    assert EMAIL not in capture.raw()


def test_decision_structure_is_preserved(capture):
    log_decision(_event())
    (line,) = capture.lines()
    assert line["logger"] == "trust.decisions"
    assert line["msg"].startswith("decision review hook=checkout customer=")
    d = line["decision"]
    assert d["decision_id"] == "dec-77" and d["outcome"] == "review"
    assert d["reason_codes"] == ["device_mismatch"] and d["amount"] == 88.25
    assert d["card_bin"] == "[redacted]"
    assert "customer_email" not in d


def test_every_record_is_still_written(capture):
    for n in range(5):
        log_decision(_event(decision_id=f"dec-{n}"))
    log_risk_failure(EMAIL, "4111111111111111", "boom")
    lines = capture.lines()
    assert [ln["logger"] for ln in lines] == ["trust.decisions"] * 5 + ["trust.risk"]
    assert lines[-1]["attempt"] == 1


def test_numeric_args_still_format(capture):
    logging.getLogger("trust.decisions").info("latency %d ms over budget %.1f", 212, 150.0)
    (line,) = capture.lines()
    assert line["msg"] == "latency 212 ms over budget 150.0"


def test_redaction_is_attached_where_every_record_passes(capture):
    """The handler that writes decisions.log must itself redact (or every logger that can
    reach it must): checked by emitting straight through the handler."""
    record = logging.LogRecord("trust.x", logging.INFO, __file__, 1, "mail %s", (EMAIL,), None)
    capture.handler.handle(record)
    assert EMAIL not in capture.raw()
    assert any(isinstance(f, RedactingFilter) for f in capture.handler.filters) or EMAIL not in capture.raw()


def test_trust_records_stay_out_of_the_root_log(capture):
    seen: list[logging.LogRecord] = []

    class Spy(logging.Handler):
        def emit(self, record):
            seen.append(record)

    spy = Spy()
    logging.getLogger().addHandler(spy)
    try:
        log_decision(_event())
    finally:
        logging.getLogger().removeHandler(spy)
    assert seen == []
