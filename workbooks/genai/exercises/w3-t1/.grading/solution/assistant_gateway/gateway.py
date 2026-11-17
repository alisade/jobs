"""LLM gateway used by the shopping assistant: one entry point, retries, fallback model, cost log.

Reference solution: timeout sized to the answer budget, retries only on transient errors with
backoff and jitter, one attempt budget shared by primary and fallback, a per-request cost cap, and
every attempt logged with what it (probably) cost.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

from .clock import Clock
from .pricing import cost_usd
from .provider import (
    Completion,
    FakeProvider,
    InvalidRequest,
    ProviderError,
    ProviderTimeout,
    RateLimited,
    count_tokens,
)

log = logging.getLogger("gateway")


class GatewayError(Exception):
    """No answer could be produced; the assistant shows a friendly error."""


class BudgetExceeded(GatewayError):
    """The request hit its per-request cost cap."""


@dataclass
class GatewayConfig:
    primary: str = "primary"
    fallback: str = "fallback"
    timeout_floor_s: float = 5.0
    min_tokens_per_s: float = 100.0   # slowest output rate we plan for
    timeout_cap_s: float = 120.0
    max_attempts: int = 3             # total model calls per request, primary + fallback
    max_cost_usd: float = 0.25        # per request, including attempts we discarded
    backoff_base_s: float = 0.5
    backoff_cap_s: float = 8.0

    def timeout_for(self, max_tokens: int) -> float:
        return min(self.timeout_cap_s, self.timeout_floor_s + max_tokens / self.min_tokens_per_s)


@dataclass
class Gateway:
    provider: FakeProvider
    clock: Clock
    config: GatewayConfig = field(default_factory=GatewayConfig)
    rng: random.Random = field(default_factory=lambda: random.Random(7))
    attempt_log: list = field(default_factory=list)

    def _backoff(self, n: int, retry_after: float | None) -> float:
        ceiling = min(self.config.backoff_cap_s, self.config.backoff_base_s * 2 ** (n - 1))
        delay = ceiling / 2 + self.rng.uniform(0, ceiling / 2)  # equal jitter
        if retry_after is not None:
            delay = max(delay, retry_after)
        return delay

    def _log(self, conv: str, model: str, attempt: int, outcome: str, inp: int, out: int,
             cost: float, discarded: bool) -> None:
        entry = {"conversation_id": conv, "model": model, "attempt": attempt, "outcome": outcome,
                 "input_tokens": inp, "output_tokens": out, "cost_usd": cost, "discarded": discarded}
        self.attempt_log.append(entry)
        log.info("attempt %s", entry)

    def answer(self, conversation_id: str, messages: list[dict], max_tokens: int = 2048) -> Completion:
        cfg = self.config
        timeout = cfg.timeout_for(max_tokens)
        model = cfg.primary
        spent = 0.0
        same_model_failures = 0
        last_error: Exception | None = None
        for attempt in range(1, cfg.max_attempts + 1):
            if spent >= cfg.max_cost_usd:
                raise BudgetExceeded(f"spent ${spent:.4f} of ${cfg.max_cost_usd:.2f} on conversation {conversation_id}")
            try:
                c = self.provider.create(model=model, messages=messages, max_tokens=max_tokens, timeout=timeout)
            except InvalidRequest as e:
                self._log(conversation_id, model, attempt, "invalid_request", 0, 0, 0.0, True)
                raise GatewayError(f"request rejected: {e}") from e
            except ProviderTimeout as e:
                # The provider probably finished and billed it: count the worst case.
                est = cost_usd(model, count_tokens(messages), max_tokens)
                spent += est
                self._log(conversation_id, model, attempt, "timeout", count_tokens(messages), max_tokens, est, True)
                last_error = e
                model, same_model_failures = cfg.fallback, 0  # same request, same model: do not repeat it
                continue
            except ProviderError as e:  # 429, 529 and other transient errors are not billed
                self._log(conversation_id, model, attempt, "rate_limited" if isinstance(e, RateLimited) else "overloaded",
                          0, 0, 0.0, True)
                last_error = e
                same_model_failures += 1
                if attempt == cfg.max_attempts:
                    break
                if model == cfg.primary and attempt == cfg.max_attempts - 1:
                    model, same_model_failures = cfg.fallback, 0
                self.clock.sleep(self._backoff(attempt, getattr(e, "retry_after", None)))
                continue
            cost = cost_usd(model, c.input_tokens, c.output_tokens)
            spent += cost
            self._log(conversation_id, model, attempt, "ok", c.input_tokens, c.output_tokens, cost, False)
            return c
        raise GatewayError(f"no answer after {cfg.max_attempts} attempts: {last_error}")
