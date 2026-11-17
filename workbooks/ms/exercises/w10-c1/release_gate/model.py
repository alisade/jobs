"""Test-set model and loader. Provided; you should not need to change this file."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class TestCase:
    __test__ = False  # not a pytest test class

    id: str
    category: str
    utterance: str
    expected_tool: str | None = None          # tool the agent should invoke FIRST; None = no tool expected
    allowed_sources: tuple[str, ...] = ()     # knowledge sources a grounded answer may cite
    must_refuse: bool = False                 # injection / out-of-scope: agent must refuse and call no tool
    expected_facts: tuple[str, ...] = ()      # facts that must appear in the final answer
    tags: tuple[str, ...] = field(default=())


def load_testset(path: str | Path) -> list[TestCase]:
    cases: list[TestCase] = []
    seen: set[str] = set()
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if raw["id"] in seen:
            raise ValueError(f"{path}:{n}: duplicate test case id {raw['id']}")
        seen.add(raw["id"])
        cases.append(
            TestCase(
                id=raw["id"],
                category=raw["category"],
                utterance=raw["utterance"],
                expected_tool=raw.get("expected_tool"),
                allowed_sources=tuple(raw.get("allowed_sources", [])),
                must_refuse=bool(raw.get("must_refuse", False)),
                expected_facts=tuple(raw.get("expected_facts", [])),
                tags=tuple(raw.get("tags", [])),
            )
        )
    return cases
