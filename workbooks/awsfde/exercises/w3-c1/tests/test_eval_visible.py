"""Visible checks for w3-c1 (happy paths). The grader runs more."""

from __future__ import annotations

from kb_eval.harness import recall_at_k, reciprocal_rank, unique_ranked_uris
from kb_eval.request import build_retrieve_request


def test_tenant_filter_alone():
    req = build_retrieve_request("KBTIDEWATER01", "acme-foods", "pallet specs?")
    vsc = req["retrievalConfiguration"]["vectorSearchConfiguration"]
    assert vsc["filter"] == {"equals": {"key": "tenant_id", "value": "acme-foods"}}
    assert vsc["numberOfResults"] == 5
    assert req["retrievalQuery"] == {"text": "pallet specs?"}


def test_metrics_simple():
    ranked = ["a", "b", "c"]
    assert recall_at_k(["b", "z"], ranked, 5) == 0.5
    assert reciprocal_rank(["c"], ranked) == 1 / 3


def test_dedupe_chunks():
    r = [{"location": {"s3Location": {"uri": u}}} for u in ["a", "a", "b"]]
    assert unique_ranked_uris(r) == ["a", "b"]
