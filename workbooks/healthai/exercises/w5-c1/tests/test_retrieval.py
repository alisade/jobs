from retrieval.evaluate import recall_at_k, reciprocal_rank


def test_metrics_small_cases():
    assert recall_at_k(["a", "b", "c"], "b", 2) == 1.0
    assert recall_at_k(["a", "b", "c"], "c", 2) == 0.0
    assert reciprocal_rank(["a", "b", "c"], "b") == 0.5


def test_exact_policy_id_query_finds_the_section(retriever):
    res = retriever.retrieve("KHP-MP-0101 reauthorization", lob="commercial", as_of="2026-11-01", k=5)
    assert "KHP-MP-0101-v3-reauth" in res


def test_retired_version_is_never_returned(retriever):
    res = retriever.retrieve("KHP-MP-0417 step", lob="commercial", as_of="2026-11-01", k=10)
    assert "KHP-MP-0417-v2-step" not in res
