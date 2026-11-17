"""Helpers for the visible tests."""

from __future__ import annotations

from pathlib import Path

from agentloop.replay import load

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "recorded_turns.jsonl"


def recorded_turns():
    return load(FIXTURES)
