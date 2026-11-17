"""A consecutive-failure circuit breaker in front of the risk client.

Closed: calls pass. After ``failures`` consecutive failures it opens for ``reset_s``
seconds: calls fail immediately with BreakerOpen (no network, ~0 ms), and the hook's fail
policy decides what that means. After ``reset_s`` one trial call is let through
(half-open); success closes the breaker, failure re-opens it.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class BreakerOpen(Exception):
    """Raised instead of calling the risk API while the breaker is open."""


class CircuitBreaker:
    def __init__(
        self, failures: int = 5, reset_s: float = 30.0, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._threshold = failures
        self._reset_s = reset_s
        self._clock = clock
        self._consecutive = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        if self._clock() - self._opened_at >= self._reset_s:
            return "half_open"
        return "open"

    def check(self) -> None:
        if self.state == "open":
            raise BreakerOpen("risk API circuit open")

    def record_success(self) -> None:
        self._consecutive = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._consecutive += 1
        if self.state == "half_open" or self._consecutive >= self._threshold:
            self._opened_at = self._clock()
