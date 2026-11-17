"""Hybrid routing between the local model and an optional cloud model. TODO: answer()."""

from __future__ import annotations

from dataclasses import dataclass

from . import agent

COMPLEX_HINTS = ("compare", "why", "trend", "root cause", "explain")


@dataclass(frozen=True)
class Policy:
    allow_cloud: bool = False
    cloud_for_complex: bool = False


def is_complex(question: str) -> bool:
    q = question.lower()
    return len(q) > 160 or sum(h in q for h in COMPLEX_HINTS) >= 2


def answer(question: str, local, cloud, policy: Policy) -> agent.AgentResult:
    raise NotImplementedError("TODO")
