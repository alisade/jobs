"""Retrieval eval harness: recall@k, MRR, per-tenant breakdown, cross-tenant leak check, gate."""

from __future__ import annotations

from typing import Any

from .request import build_retrieve_request


def result_uri(result: dict) -> str:
    """S3 URI of one retrievalResults entry (done)."""
    return result["location"]["s3Location"]["uri"]


def unique_ranked_uris(results: list[dict]) -> list[str]:
    """Document URIs in rank order with duplicate chunks of the same document removed.

    TODO
    """
    raise NotImplementedError


def recall_at_k(expected: list[str], ranked: list[str], k: int) -> float:
    """Share of expected documents found in the first k unique documents. TODO"""
    raise NotImplementedError


def reciprocal_rank(expected: list[str], ranked: list[str]) -> float:
    """1 / rank of the first expected document in the unique ranking, 0.0 if none. TODO"""
    raise NotImplementedError


def leaks(tenant_id: str, results: list[dict]) -> list[str]:
    """URIs of results that do not belong to the caller's tenant.

    TODO: a result whose metadata tenant_id differs, or is missing, is a leak.
    """
    raise NotImplementedError


def evaluate(client: Any, kb_id: str, golden: list[dict], k: int = 5, config_name: str = "") -> dict:
    """Run every golden question through Retrieve and build the report.

    TODO: report = {
      "config": config_name, "k": k, "questions": n,
      "recall_at_k": mean, "mrr": mean,
      "per_tenant": {tenant: {"questions", "recall_at_k", "mrr"}},
      "leaks": [{"id", "tenant_id", "uris"}],
      "per_question": [{"id", "tenant_id", "recall_at_k", "rr", "ranked"}],
    }
    Means rounded to 4 decimals.
    """
    raise NotImplementedError


def compare(baseline: dict, candidate: dict) -> dict:
    """Deltas (candidate - baseline) for recall_at_k and mrr, overall and per tenant. TODO"""
    raise NotImplementedError


def gate(report: dict, min_recall: float = 0.8, min_mrr: float = 0.6,
         min_tenant_recall: float = 0.7) -> tuple[bool, list[str]]:
    """Go/no-go for promoting a KB config. Any leak is an automatic no-go. TODO"""
    raise NotImplementedError
