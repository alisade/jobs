"""Token usage accounting and cost estimate per turn."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    model_calls: int = 0
    latency_ms: int = 0
    per_call: list[dict] = field(default_factory=list)

    def add(self, response: dict) -> None:
        """Add one Converse response's usage and metrics."""
        u = response.get("usage", {})
        rec = {
            "input_tokens": int(u.get("inputTokens", 0)),
            "output_tokens": int(u.get("outputTokens", 0)),
            "cache_read_tokens": int(u.get("cacheReadInputTokens", 0)),
            "cache_write_tokens": int(u.get("cacheWriteInputTokens", 0)),
            "latency_ms": int(response.get("metrics", {}).get("latencyMs", 0)),
            "stop_reason": response.get("stopReason"),
        }
        self.input_tokens += rec["input_tokens"]
        self.output_tokens += rec["output_tokens"]
        self.cache_read_tokens += rec["cache_read_tokens"]
        self.cache_write_tokens += rec["cache_write_tokens"]
        self.latency_ms += rec["latency_ms"]
        self.model_calls += 1
        self.per_call.append(rec)


def estimate_cost_usd(usage: Usage, model_id: str, prices_per_1k: dict) -> float:
    """Estimated USD cost of the turn from the price table in config.json."""
    p = prices_per_1k[model_id]  # KeyError for an unknown model: never price it at zero
    total = (
        usage.input_tokens * p["input"]
        + usage.output_tokens * p["output"]
        + usage.cache_read_tokens * p.get("cache_read", p["input"])
        + usage.cache_write_tokens * p.get("cache_write", p["input"])
    ) / 1000.0
    return round(total, 6)
