"""Scores for the eval dashboard: overall accuracy, exception recall, cost."""

from __future__ import annotations


def score(golden: dict[str, dict], runs: list[dict]) -> dict:
    scored = [r for r in runs if r["sample_id"] in golden]
    ok = sum(1 for r in scored if r["overall"] == golden[r["sample_id"]]["overall"])
    tp = sum(1 for r in scored if r["overall"] == "exception" and golden[r["sample_id"]]["overall"] == "exception")
    pos = sum(1 for r in scored if golden[r["sample_id"]]["overall"] == "exception")
    missed = sorted(r["sample_id"] for r in scored if golden[r["sample_id"]]["overall"] == "exception" and r["overall"] != "exception")
    return {
        "samples": len(scored),
        "accuracy": ok / len(scored) if scored else None,
        "exception_recall": tp / pos if pos else None,
        "exceptions_in_golden": pos,
        "missed_exceptions": missed,
    }


def cost_per_100(runs: list[dict], prices: dict) -> float:
    total = 0.0
    for r in runs:
        u = r["usage"]
        fresh = u["prompt_tokens"] - u["cached_tokens"]
        total += (fresh * prices["input"] + u["cached_tokens"] * prices["cached_input"] + u["output_tokens"] * prices["output"]) / 1_000
    return 100 * total / len(runs) if runs else 0.0
