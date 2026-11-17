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
        """Add one Converse response's usage and metrics.

        TODO: read response["usage"] (inputTokens, outputTokens, and the optional
        cacheReadInputTokens / cacheWriteInputTokens) and response["metrics"]["latencyMs"];
        accumulate them and append a per-call record.
        """
        raise NotImplementedError


def estimate_cost_usd(usage: Usage, model_id: str, prices_per_1k: dict) -> float:
    """Estimated USD cost of the turn from the price table in config.json.

    TODO: input, output, cache read and cache write tokens each at their own price.
    An unknown model id must raise KeyError (do not silently price it at zero).
    Round to 6 decimal places.
    """
    raise NotImplementedError
