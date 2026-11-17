"""Bedrock on-demand quota model: a token bucket per model per Region (requests per minute).

Every attempt that reaches Bedrock costs one token, including attempts that get throttled
(they still count as InvocationThrottles). Numbers are illustrative, chosen to match the
account's applied quota of ~290 RPM (4.8 requests per second) for this model with a short burst allowance.
"""

from __future__ import annotations


class TokenBucket:
    def __init__(self, rate_per_s: float = 4.8, burst: float = 30.0) -> None:
        self.rate = rate_per_s
        self.capacity = burst
        self.tokens = burst
        self.t = 0.0

    def take(self, now: float) -> bool:
        self.tokens = min(self.capacity, self.tokens + (now - self.t) * self.rate)
        self.t = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False
