from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.WARNING)

from tester import systems  # noqa: E402

SAMPLE = ["CHG-104118", "CHG-104163", "CHG-104390"]


@pytest.fixture(autouse=True)
def clear_executed():
    systems.EXECUTED.clear()
    yield


def run(coro, timeout=30):
    return asyncio.run(asyncio.wait_for(coro, timeout))
