"""Retrieval eval harness: recall@k, MRR, per-tenant breakdown, cross-tenant leak check, gate."""

from __future__ import annotations

from typing import Any

from .request import build_retrieve_request


def result_uri(result: dict) -> str:
    """S3 URI of one retrievalResults entry (done)."""
    return result["location"]["s3Location"]["uri"]


def unique_ranked_uris(results: list[dict]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for r in results:
        u = result_uri(r)
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def recall_at_k(expected: list[str], ranked: list[str], k: int) -> float:
    exp = set(expected)
    if not exp:
        raise ValueError("a golden question needs at least one expected document")
    return len(exp & set(ranked[:k])) / len(exp)


def reciprocal_rank(expected: list[str], ranked: list[str]) -> float:
    exp = set(expected)
    for i, u in enumerate(ranked, start=1):
        if u in exp:
            return 1.0 / i
    return 0.0


def leaks(tenant_id: str, results: list[dict]) -> list[str]:
    out = []
    for r in results:
        if (r.get("metadata") or {}).get("tenant_id") != tenant_id:
            u = result_uri(r)
            if u not in out:
                out.append(u)
    return out


def _mean(xs: list[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def evaluate(client: Any, kb_id: str, golden: list[dict], k: int = 5, config_name: str = "") -> dict:
    per_q, found_leaks = [], []
    for q in golden:
        req = build_retrieve_request(kb_id, q["tenant_id"], q["question"], None, k)
        results = client.retrieve(**req).get("retrievalResults", [])
        ranked = unique_ranked_uris(results)
        lk = leaks(q["tenant_id"], results)
        if lk:
            found_leaks.append({"id": q["id"], "tenant_id": q["tenant_id"], "uris": lk})
        per_q.append({"id": q["id"], "tenant_id": q["tenant_id"],
                      "recall_at_k": recall_at_k(q["expected_uris"], ranked, k),
                      "rr": reciprocal_rank(q["expected_uris"], ranked), "ranked": ranked})
    tenants: dict[str, dict] = {}
    for p in per_q:
        t = tenants.setdefault(p["tenant_id"], {"r": [], "rr": []})
        t["r"].append(p["recall_at_k"])
        t["rr"].append(p["rr"])
    return {
        "config": config_name, "k": k, "questions": len(per_q),
        "recall_at_k": _mean([p["recall_at_k"] for p in per_q]),
        "mrr": _mean([p["rr"] for p in per_q]),
        "per_tenant": {t: {"questions": len(v["r"]), "recall_at_k": _mean(v["r"]), "mrr": _mean(v["rr"])}
                       for t, v in sorted(tenants.items())},
        "leaks": found_leaks,
        "per_question": per_q,
    }


def compare(baseline: dict, candidate: dict) -> dict:
    tenants = sorted(set(baseline["per_tenant"]) | set(candidate["per_tenant"]))
    def d(a: dict, b: dict, key: str) -> float:
        return round(b.get(key, 0.0) - a.get(key, 0.0), 4)
    return {
        "baseline": baseline.get("config"), "candidate": candidate.get("config"),
        "recall_at_k": d(baseline, candidate, "recall_at_k"),
        "mrr": d(baseline, candidate, "mrr"),
        "per_tenant": {t: {"recall_at_k": d(baseline["per_tenant"].get(t, {}), candidate["per_tenant"].get(t, {}), "recall_at_k"),
                           "mrr": d(baseline["per_tenant"].get(t, {}), candidate["per_tenant"].get(t, {}), "mrr")}
                       for t in tenants},
        "leaks": {"baseline": len(baseline["leaks"]), "candidate": len(candidate["leaks"])},
    }


def gate(report: dict, min_recall: float = 0.8, min_mrr: float = 0.6,
         min_tenant_recall: float = 0.7) -> tuple[bool, list[str]]:
    reasons = []
    if report["leaks"]:
        reasons.append(f"cross-tenant results in {len(report['leaks'])} question(s)")
    if report["recall_at_k"] < min_recall:
        reasons.append(f"recall@{report['k']} {report['recall_at_k']} < {min_recall}")
    if report["mrr"] < min_mrr:
        reasons.append(f"mrr {report['mrr']} < {min_mrr}")
    for t, v in report["per_tenant"].items():
        if v["recall_at_k"] < min_tenant_recall:
            reasons.append(f"{t} recall@{report['k']} {v['recall_at_k']} < {min_tenant_recall}")
    return (not reasons), reasons
