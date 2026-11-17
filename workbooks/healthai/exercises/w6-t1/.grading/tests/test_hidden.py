"""Hidden tests for healthai/w6-t1: every way of logging is redacted, spans included."""

import io
import json
import logging
from pathlib import Path

import pytest

from app.logsetup import build_logger
from app.pipeline import run
from app.redact import MEMBER, roster_names
from app.tracing import TRACER

EX = Path(__file__).resolve().parent.parent
NAME, MEMBER_ID = "Ruairi Fenwick-Obi", "M-100417"


def leaks(text):
    low = text.lower()
    return bool(MEMBER.search(text)) or any(n.lower() in low for n in roster_names())


@pytest.fixture
def logger():
    s = io.StringIO()
    return build_logger(s), s


@pytest.mark.parametrize("call", [
    lambda log: log.info("case for %s (%s)", NAME, MEMBER_ID),
    lambda log: log.info("case for %(n)s", {"n": NAME}),
    lambda log: log.info(f"case for {NAME} {MEMBER_ID}"),
    lambda log: log.info("note", extra={"member_name": NAME}),
    lambda log: log.info("note", extra={"reviewer_note": f"call {NAME} at (555) 201-7788"}),
])
def test_every_logging_style_is_redacted(logger, call):
    log, s = logger
    call(log)
    assert not leaks(s.getvalue()), s.getvalue()
    assert "[NAME]" in s.getvalue() or "[MEMBER]" in s.getvalue()


def test_exception_text_is_redacted(logger):
    log, s = logger
    try:
        raise LookupError(f"no coverage for {NAME} {MEMBER_ID}")
    except LookupError:
        log.exception("lookup failed for %s", NAME)
    assert not leaks(s.getvalue())
    assert "LookupError" in s.getvalue()


def test_span_events_redacted_for_args(logger):
    log, _ = logger
    TRACER.reset()
    with TRACER.span("pa.assess", **{"khp.case_id": "PA-1"}):
        log.warning("eligibility retry for %s member %s", NAME, MEMBER_ID)
    assert not leaks(json.dumps(TRACER.export()))


def test_messages_still_useful(logger):
    log, s = logger
    log.info("eligibility retry for %s member %s", NAME, MEMBER_ID, extra={"case_id": "PA-9"})
    rec = json.loads(s.getvalue().splitlines()[-1])
    assert rec["message"] == "eligibility retry for [NAME] member [MEMBER]"
    assert rec["case_id"] == "PA-9"


def test_pipeline_clean_end_to_end(tmp_path):
    run(out_dir=tmp_path)
    lines = (tmp_path / "app.log.jsonl").read_text().splitlines()
    spans = json.loads((tmp_path / "spans.json").read_text())
    assert len(lines) > 600 and len(spans) == 300
    assert not any(leaks(l) for l in lines)
    assert not any(leaks(json.dumps(sp)) for sp in spans)


def test_span_attributes_guard(tmp_path):
    run(out_dir=tmp_path)
    spans = json.loads((tmp_path / "spans.json").read_text())
    assert all(sp["attributes"]["khp.member"] == "[MEMBER]" for sp in spans)


def test_findings():
    f = json.loads((EX / "findings.json").read_text())
    assert f["root_cause_file"].endswith("logsetup.py")
    assert f["root_cause_class"] == "RedactFilter"
    assert "%s" in f["leaking_log_call"] and "retry" in f["leaking_log_call"]
    assert f["span_leak_percent_before"] == pytest.approx(3.3, abs=0.2)
    assert "nested" in f["red_herring"].lower() or "scrub_attributes" in f["red_herring"]
