"""Hidden tests for healthai/w5-c1."""

import math
from datetime import date

import pytest

from retrieval.evaluate import evaluate, recall_at_k, reciprocal_rank
from retrieval.rerank import StubReranker
from retrieval.search import BM25Index, HybridRetriever, allowed_ids, rrf

TOY = [
    {"id": "d1", "text": "lumbar mri criteria radiculopathy", "lobs": ["commercial"], "effective_from": "2026-01-01", "effective_to": None},
    {"id": "d2", "text": "knee arthroscopy criteria", "lobs": ["commercial"], "effective_from": "2026-01-01", "effective_to": None},
    {"id": "d3", "text": "lumbar lumbar spine step therapy conservative trial weeks", "lobs": ["medicaid-mco"], "effective_from": "2024-01-01", "effective_to": "2026-01-01"},
]


def bm25_ref(query, docs, k1=1.5, b=0.75):
    toks = [d["text"].split() for d in docs]
    n, avg = len(docs), sum(map(len, toks)) / len(docs)
    out = {}
    for d, t in zip(docs, toks):
        s = 0.0
        for q in query.split():
            df = sum(1 for x in toks if q in x)
            f = t.count(q)
            if f:
                s += math.log(1 + (n - df + 0.5) / (df + 0.5)) * f * (k1 + 1) / (f + k1 * (1 - b + b * len(t) / avg))
        out[d["id"]] = s
    return out


def test_bm25_scores_match_okapi():
    ref = bm25_ref("lumbar criteria", TOY)
    got = dict(BM25Index(TOY).search("lumbar criteria", k=10))
    for i, v in ref.items():
        if v > 0:
            assert got[i] == pytest.approx(v, rel=1e-6)


def test_bm25_term_frequency_saturates_and_idf_matters():
    got = BM25Index(TOY).search("lumbar radiculopathy", k=3)
    assert got[0][0] == "d1"  # the rare term beats repeated common term


def test_bm25_respects_allowed_and_drops_zero():
    got = BM25Index(TOY).search("lumbar", k=10, allowed={"d1", "d2"})
    assert [d for d, _ in got] == ["d1"]


def test_rrf_formula_and_order():
    got = rrf([["a", "b"], ["b", "c"]])
    assert [d for d, _ in got] == ["b", "a", "c"]
    assert dict(got)["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert dict(rrf([["a"]], k=10))["a"] == pytest.approx(1 / 11)


def test_allowed_ids_lob_and_dates():
    assert allowed_ids(TOY, "commercial", "2026-11-01") == {"d1", "d2"}
    assert allowed_ids(TOY, "medicaid-mco", "2025-06-01") == {"d3"}
    assert allowed_ids(TOY, "medicaid-mco", "2026-01-01") == set()  # end date is exclusive
    assert allowed_ids(TOY, "commercial", "2025-12-31") == set()    # not yet effective


def test_no_retired_or_wrong_lob_in_any_mode(retriever, docs, queries):
    by = {d["id"]: d for d in docs}
    for mode in ("bm25", "dense", "hybrid"):
        for q in queries:
            for r in retriever.retrieve(q["text"], lob=q["lob"], as_of=q["as_of"], k=10, mode=mode):
                d = by[r]
                assert q["lob"] in d["lobs"], (mode, q["id"], r)
                end = d.get("effective_to")
                assert not end or date.fromisoformat(end) > date.fromisoformat(q["as_of"]), (mode, q["id"], r)


def test_filter_before_ranking_keeps_k_results(retriever):
    res = retriever.retrieve("KHP-MP-0417 lumbar spine mri", lob="commercial", as_of="2026-11-01", k=6, mode="bm25")
    assert len(res) == 6 and all("-v3-" in r for r in res)


def test_metrics():
    assert recall_at_k(["a", "b"], {"a", "z"}, 2) == 0.5
    assert reciprocal_rank(["x", "y", "a"], "a") == pytest.approx(1 / 3)
    assert reciprocal_rank(["x"], "a") == 0.0


class Fixed:
    def __init__(self, table):
        self.table = table

    def retrieve(self, text, lob=None, as_of=None, k=10, **kw):
        return self.table[text]


def test_evaluate_structure_and_slices():
    qs = [{"id": "1", "text": "q1", "gold": "a", "kind": "exact"},
          {"id": "2", "text": "q2", "gold": "b", "kind": "paraphrase"}]
    out = evaluate(Fixed({"q1": ["a", "x"], "q2": ["x", "y", "b"]}), qs, k=2)
    assert out["recall@2"] == 0.5 and out["n"] == 2
    assert out["mrr"] == pytest.approx((1 + 1 / 3) / 2)
    assert out["by_kind"]["exact"]["recall@2"] == 1.0
    assert out["by_kind"]["paraphrase"]["recall@2"] == 0.0


def test_hybrid_beats_both_single_methods(retriever, queries):
    bm = evaluate(retriever, queries, k=5, mode="bm25")["recall@5"]
    de = evaluate(retriever, queries, k=5, mode="dense")["recall@5"]
    hy = evaluate(retriever, queries, k=5, mode="hybrid")["recall@5"]
    assert hy >= 0.95 and hy >= bm + 0.25 and hy >= de + 0.1, (bm, de, hy)


def test_slices_show_why(retriever, queries):
    bm = evaluate(retriever, queries, k=5, mode="bm25")["by_kind"]
    de = evaluate(retriever, queries, k=5, mode="dense")["by_kind"]
    assert bm["exact"]["recall@5"] > de["exact"]["recall@5"]
    assert de["paraphrase"]["recall@5"] > bm["paraphrase"]["recall@5"]


def test_rerank_improves_mrr_and_is_bounded(docs, queries):
    rr = StubReranker()
    r = HybridRetriever(docs, reranker=rr, rerank_top_n=20)
    base = evaluate(r, queries, k=5, mode="hybrid")["mrr"]
    rr.pairs_scored = 0
    top = evaluate(r, queries, k=5, mode="hybrid", rerank=True)["mrr"]
    assert top >= 0.95 and top >= base + 0.05, (base, top)
    assert 0 < rr.pairs_scored <= 20 * len(queries)


def test_unknown_mode(retriever):
    with pytest.raises(ValueError):
        retriever.retrieve("x", mode="sparse-ish")
