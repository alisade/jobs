"""Application-level retry helper (added in release 2026.11.06)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from botocore.exceptions import ClientError


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5            # total attempts made by this layer, including the first
    base_delay: float = 1.0          # seconds
    max_delay: float = 1.0           # seconds; cap on a single delay
    jitter: bool = False
    retryable_codes: frozenset | None = None   # None = retry every ClientError

    def should_retry(self, code: str, attempt: int) -> bool:
        """attempt is the 1-based number of the attempt that just failed."""
        if attempt >= self.max_attempts:
            return False
        return self.retryable_codes is None or code in self.retryable_codes

    def delay(self, attempt: int, rng: Callable[[], float]) -> float:
        """Seconds to wait after failed attempt number `attempt` (1-based)."""
        d = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
        return rng() * d if self.jitter else d


# "Be resilient: never give up on the first error." -- release 2026.11.06
APP_POLICY = RetryPolicy(max_attempts=5, base_delay=1.0, max_delay=1.0, jitter=False, retryable_codes=None)


def call_with_retries(fn: Callable[[], Any], policy: RetryPolicy, sleep: Callable[[float], None],
                      rng: Callable[[], float]) -> Any:
    attempt = 1
    while True:
        try:
            return fn()
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            if not policy.should_retry(code, attempt):
                raise
            sleep(policy.delay(attempt, rng))
            attempt += 1
