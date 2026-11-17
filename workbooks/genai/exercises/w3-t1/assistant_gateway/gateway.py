"""LLM gateway used by the shopping assistant: one entry point, retries, fallback model, cost log.

This is the version in production since release 2026.11.10 (see evidence/release-notes.md).
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

from .clock import Clock
from .pricing import cost_usd
from .provider import Completion, FakeProvider, ProviderError

log = logging.getLogger("gateway")


class GatewayError(Exception):
    """No answer could be produced; the assistant shows a friendly error."""


class BudgetExceeded(GatewayError):
    """The request hit its per-request cost cap."""


@dataclass
class GatewayConfig:
    primary: str = "primary"
    fallback: str = "fallback"
    timeout_s: float = 10.0
    retries: int = 3
    max_attempts: int = 3          # total model calls per request, primary + fallback
    max_cost_usd: float = 0.25     # per request
    backoff_base_s: float = 0.5
    backoff_cap_s: float = 8.0


@dataclass
class Gateway:
    provider: FakeProvider
    clock: Clock
    config: GatewayConfig = field(default_factory=GatewayConfig)
    rng: random.Random = field(default_factory=lambda: random.Random(7))
    attempt_log: list = field(default_factory=list)

    def answer(self, conversation_id: str, messages: list[dict], max_tokens: int = 2048) -> Completion:
        for model in (self.config.primary, self.config.fallback):
            for attempt in range(1, self.config.retries + 2):
                try:
                    c = self.provider.create(model=model, messages=messages, max_tokens=max_tokens,
                                             timeout=self.config.timeout_s)
                except ProviderError as e:
                    log.warning("conv=%s model=%s attempt=%d %s", conversation_id, model, attempt, e)
                    continue
                self.attempt_log.append({
                    "conversation_id": conversation_id, "model": model, "attempt": attempt,
                    "outcome": "ok", "input_tokens": c.input_tokens, "output_tokens": c.output_tokens,
                    "cost_usd": cost_usd(model, c.input_tokens, c.output_tokens), "discarded": False,
                })
                return c
        raise GatewayError("all models failed")
