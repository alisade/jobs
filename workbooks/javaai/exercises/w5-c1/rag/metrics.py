"""Retrieval metrics at section level: several chunks of one section count once."""

from __future__ import annotations


def dedupe(section_ids: list[str]) -> list[str]:
    """Keep the first occurrence of each id, preserving rank order. TODO(w5-c1)"""
    return section_ids


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant sections found in the top k distinct sections. TODO(w5-c1)"""
    return 0.0


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    """1 / rank of the first relevant distinct section (1-based); 0 if none. TODO(w5-c1)"""
    return 0.0
