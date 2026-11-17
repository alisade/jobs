"""Retrieval metrics and an eval harness."""

from __future__ import annotations


def recall_at_k(results: list[str], gold: str | set[str], k: int) -> float:
    g = {gold} if isinstance(gold, str) else set(gold)
    return len(g & set(results[:k])) / len(g) if g else 0.0


def reciprocal_rank(results: list[str], gold: str | set[str]) -> float:
    g = {gold} if isinstance(gold, str) else set(gold)
    for i, r in enumerate(results, start=1):
        if r in g:
            return 1.0 / i
    return 0.0


def evaluate(retriever, queries: list[dict], k: int = 5, **kwargs) -> dict:
    """{"recall@k": float, "mrr": float, "n": int, "by_kind": {kind: {"recall@k", "mrr", "n"}}}"""
    rows = []
    for q in queries:
        res = retriever.retrieve(q["text"], lob=q.get("lob"), as_of=q.get("as_of"), k=max(k, 10), **kwargs)
        rows.append((q.get("kind", "all"), recall_at_k(res, q["gold"], k), reciprocal_rank(res, q["gold"])))

    def agg(rs):
        return {f"recall@{k}": sum(r for _, r, _ in rs) / len(rs) if rs else 0.0,
                "mrr": sum(m for _, _, m in rs) / len(rs) if rs else 0.0, "n": len(rs)}

    out = agg(rows)
    out["by_kind"] = {kind: agg([r for r in rows if r[0] == kind]) for kind in sorted({r[0] for r in rows})}
    return out
