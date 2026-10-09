"""Fixtures for the visible tests; the helpers live in aic1_hidden_support.py."""

from __future__ import annotations

import pytest
from aic1_hidden_support import VERDICTS

from evals.fake_judge import FakeJudgeClient


@pytest.fixture
def judge():
    return FakeJudgeClient.from_file(VERDICTS)
