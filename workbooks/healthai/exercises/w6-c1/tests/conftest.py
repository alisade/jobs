import io
import json
import logging
from pathlib import Path

import pytest

FIX = Path(__file__).resolve().parent.parent / "fixtures"
NAMES = ["Rosalind", "June", "Okafor-Benn"]


@pytest.fixture
def bundle():
    return json.loads((FIX / "bundle.json").read_text())


@pytest.fixture
def capture():
    """A logger whose handler output is returned by capture.text(); the RedactingFilter sits on the handler."""
    from deid.core import RedactingFilter

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s %(case_note)s"))
    handler.addFilter(RedactingFilter(NAMES))
    log = logging.getLogger(f"khp.test.{id(stream)}")
    log.handlers = [handler]
    log.propagate = False
    log.setLevel(logging.INFO)

    class Cap:
        logger = log

        @staticmethod
        def text():
            return stream.getvalue()

    return Cap
