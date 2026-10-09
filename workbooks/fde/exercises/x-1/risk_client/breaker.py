"""A consecutive-failure circuit breaker with a single half-open trial.

YOUR WORK GOES HERE (see README.md for the state machine). The clock is injected so
tests can move time without sleeping.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Literal

from .errors import CircuitOpen  # noqa: F401  (you will need it)

State = Literal["closed", "open", "half_open"]


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        # TODO: validate arguments (threshold >= 1, reset timeout > 0) and set up state.
        self._threshold = failure_threshold
        self._reset_timeout = reset_timeout_s
        self._clock = clock

    @property
    def state(self) -> State:
        """closed; open while the cool-down runs; half_open once it has elapsed."""
        raise NotImplementedError("CircuitBreaker.state")

    @property
    def consecutive_failures(self) -> int:
        raise NotImplementedError("CircuitBreaker.consecutive_failures")

    def before_call(self) -> None:
        """Raise CircuitOpen when the call must not go out. In half_open exactly one
        caller (the trial) gets through until it records a verdict or is released."""
        raise NotImplementedError("CircuitBreaker.before_call")

    def record_success(self) -> None:
        raise NotImplementedError("CircuitBreaker.record_success")

    def record_failure(self) -> None:
        raise NotImplementedError("CircuitBreaker.record_failure")

    def release(self) -> None:
        """Abandon a trial without a verdict (the call was cancelled)."""
        raise NotImplementedError("CircuitBreaker.release")
