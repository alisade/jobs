from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sampling import exports  # noqa: E402

START, END = date(2026, 1, 1), date(2026, 9, 30)


@pytest.fixture(scope="session")
def ex():
    return {"prs": exports.prs(), "deploys": exports.deploys(), "tickets": exports.tickets(),
            "total": exports.control_total(), "table": exports.sampling_table()}
