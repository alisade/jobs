"""Hybrid routing: local model first; cloud only when policy allows and the local path failed or the
question is complex. The cloud never sees raw waveforms: no local-only tools, no raw samples."""

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
    if policy.allow_cloud and policy.cloud_for_complex and is_complex(question):
        res = agent.run(cloud, question, include_local_only=False)
        res.model = "cloud"
        return res
    res = agent.run(local, question)
    res.model = "local"
    if res.status != "ok" and policy.allow_cloud:
        local_ms = res.latency_ms
        res = agent.run(cloud, question, include_local_only=False)
        res.model = "cloud"
        res.latency_ms += local_ms
    return res
