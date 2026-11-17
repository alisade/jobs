"""A consecutive-failure circuit breaker with a single half-open trial. Reference solution."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Literal

from .errors import CircuitOpen

State = Literal["closed", "open", "half_open"]


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if reset_timeout_s <= 0:
            raise ValueError("reset_timeout_s must be > 0")
        self._threshold = failure_threshold
        self._reset_timeout = reset_timeout_s
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None
        self._trial_in_flight = False

    @property
    def state(self) -> State:
        if self._opened_at is None:
            return "closed"
        if self._clock() - self._opened_at >= self._reset_timeout:
            return "half_open"
        return "open"

    @property
    def consecutive_failures(self) -> int:
        return self._failures

    def before_call(self) -> None:
        state = self.state
        if state == "closed":
            return
        if state == "open":
            raise CircuitOpen("risk API circuit is open")
        if self._trial_in_flight:
            raise CircuitOpen("risk API circuit is half-open; a trial call is in flight")
        self._trial_in_flight = True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._trial_in_flight = False

    def record_failure(self) -> None:
        if self._opened_at is not None:
            # A failed half-open trial (or a late failure while open): re-open, fresh cool-down.
            self._opened_at = self._clock()
            self._trial_in_flight = False
            return
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._clock()

    def release(self) -> None:
        """Abandon a trial without a verdict (the call was cancelled)."""
        self._trial_in_flight = False
