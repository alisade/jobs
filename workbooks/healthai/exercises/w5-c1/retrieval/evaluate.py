"""Retrieval metrics and an eval harness. TODO: implement (README)."""

from __future__ import annotations


def recall_at_k(results: list[str], gold: str | set[str], k: int) -> float:
    return 0.0  # TODO


def reciprocal_rank(results: list[str], gold: str | set[str]) -> float:
    return 0.0  # TODO


def evaluate(retriever, queries: list[dict], k: int = 5, **kwargs) -> dict:
    """{"recall@k": float, "mrr": float, "n": int, "by_kind": {kind: {"recall@k", "mrr", "n"}}}"""
    raise NotImplementedError
