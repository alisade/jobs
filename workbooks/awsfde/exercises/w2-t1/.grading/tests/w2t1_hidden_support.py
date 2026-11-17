"""Helpers for w2-t1: Lambda contexts shaped like the ones AgentCore Gateway sends."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from replay.gateway import make_context  # noqa: E402


def ctx(full_name: str):
    return make_context(full_name, "test-001")
