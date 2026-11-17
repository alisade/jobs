"""Application-level retry helper.

Bedrock retries live in ONE layer: the SDK client (bedrock_client.SDK_RETRIES). This module keeps
a policy object for code paths that need an explicit loop, but the default APP_POLICY makes a
single attempt so the layers never multiply. When a policy does retry, it retries only transient
errors, with exponential backoff and full jitter, and a capped delay.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from botocore.exceptions import ClientError

TRANSIENT_CODES = frozenset({
    "ThrottlingException", "ServiceUnavailableException", "InternalServerException",
    "ModelNotReadyException",
})


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1            # total attempts made by this layer, including the first
    base_delay: float = 0.5          # seconds
    max_delay: float = 4.0           # seconds; cap on a single delay
    jitter: bool = True
    retryable_codes: frozenset | None = TRANSIENT_CODES

    def should_retry(self, code: str, attempt: int) -> bool:
        """attempt is the 1-based number of the attempt that just failed."""
        if attempt >= self.max_attempts:
            return False
        return self.retryable_codes is not None and code in self.retryable_codes

    def delay(self, attempt: int, rng: Callable[[], float]) -> float:
        """Full jitter: uniform in [0, min(max_delay, base_delay * 2 ** (attempt - 1))]."""
        d = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
        return rng() * d if self.jitter else d


APP_POLICY = RetryPolicy()


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
