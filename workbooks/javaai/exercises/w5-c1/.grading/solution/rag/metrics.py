"""Retrieval metrics at section level: several chunks of one section count once."""

from __future__ import annotations


def dedupe(section_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for s in section_ids:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        raise ValueError("a labeled question needs at least one relevant section")
    top = dedupe(ranked)[:k]
    return len(relevant.intersection(top)) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for i, s in enumerate(dedupe(ranked), start=1):
        if s in relevant:
            return 1.0 / i
    return 0.0
