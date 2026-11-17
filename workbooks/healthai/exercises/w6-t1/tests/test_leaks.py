import io
import json

from app.logsetup import build_logger
from app.pipeline import run
from app.tracing import TRACER


def test_fstring_message_is_redacted():
    s = io.StringIO()
    log = build_logger(s)
    name = "Delphine Arkwright"
    log.info(f"assessing for {name}")
    assert "Arkwright" not in s.getvalue()


def test_args_message_is_redacted():
    s = io.StringIO()
    log = build_logger(s)
    log.warning("eligibility retry for %s member %s", "Delphine Arkwright", "M-100417")
    out = s.getvalue()
    assert "Arkwright" not in out and "M-100417" not in out


def test_pipeline_exports_no_identifiers(tmp_path):
    run(out_dir=tmp_path)
    blob = (tmp_path / "app.log.jsonl").read_text() + json.dumps(TRACER.export())
    assert "Vellacourt" not in blob and "Quennell" not in blob
