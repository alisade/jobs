"""Run one batch of samples and account usage, cost and latency per call. Complete."""

from __future__ import annotations

import json
from pathlib import Path

from .prompt import build_request

FIX = Path(__file__).resolve().parents[1] / "fixtures"
PRICING = json.loads((FIX / "pricing.json").read_text())


def cost_usd(model: str, prompt_tokens: int, cached_tokens: int, output_tokens: int) -> float:
    p = PRICING[model]
    return ((prompt_tokens - cached_tokens) * p["input"] + cached_tokens * p["cached_input"]
            + output_tokens * p["output"]) / 1_000_000


def run_batch(client, samples: list[dict], *, run_id: str, started_at: str, model: str = "gemini-3.8-flash-002",
              instance: str = "fn-0") -> list[dict]:
    rows = []
    for s in samples:
        contents, config = build_request(s, run_id=run_id, started_at=started_at)
        r = client.models.generate_content(model=model, contents=contents, config=config)
        um = r.usage_metadata
        cached = um.cached_content_token_count or 0
        lat = int((r.sdk_http_response.headers or {}).get("x-simulated-latency-ms", "0")) if r.sdk_http_response else 0
        rows.append({"run_id": run_id, "instance": instance, "sample_id": s["change_id"], "model_version": r.model_version,
                     "prompt_tokens": um.prompt_token_count, "cached_tokens": cached, "output_tokens": um.candidates_token_count,
                     "latency_ms": lat, "cost_usd": round(cost_usd(model, um.prompt_token_count, cached, um.candidates_token_count), 7)})
    return rows


def summarize(rows: list[dict]) -> dict:
    prompt = sum(r["prompt_tokens"] for r in rows)
    cached = sum(r["cached_tokens"] for r in rows)
    return {"calls": len(rows), "prompt_tokens": prompt, "cached_tokens": cached,
            "cache_hit_ratio": round(cached / prompt, 3) if prompt else 0.0,
            "cost_usd": round(sum(r["cost_usd"] for r in rows), 6),
            "cost_per_100_samples_usd": round(100 * sum(r["cost_usd"] for r in rows) / max(1, len(rows)), 4),
            "p50_latency_ms": sorted(r["latency_ms"] for r in rows)[len(rows) // 2] if rows else 0}
