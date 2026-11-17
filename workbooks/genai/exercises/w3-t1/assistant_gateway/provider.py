"""Local stand-in for the model provider API (do not edit).

It behaves like the real one in the ways that matter for this incident:
- Generation time grows with output length: 0.6 s + 7 ms per output token.
- If the client gives up (timeout) the provider keeps generating and STILL BILLS the request.
- 429 rate limits carry a retry-after; 529 means overloaded; 400 means the request itself is bad.
- Every billed request is recorded in `usage` (this is what finance's usage export is built from).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .clock import Clock


class ProviderError(Exception):
    status = 0


class RateLimited(ProviderError):
    status = 429

    def __init__(self, retry_after: float = 1.0) -> None:
        super().__init__(f"429 rate_limit_error (retry-after {retry_after}s)")
        self.retry_after = retry_after


class Overloaded(ProviderError):
    status = 529

    def __init__(self) -> None:
        super().__init__("529 overloaded_error")


class InvalidRequest(ProviderError):
    status = 400

    def __init__(self, message: str = "400 invalid_request_error") -> None:
        super().__init__(message)


class ProviderTimeout(ProviderError):
    """The client stopped waiting. The provider may still finish and bill the request."""

    status = 0


@dataclass
class Reply:
    """Scripted outcome for one call: a successful answer of output_tokens tokens."""

    output_tokens: int = 120
    text: str = "Here are two tents that fit."


@dataclass
class Stall:
    """Scripted outcome: the provider is slow today. Takes `seconds`, then bills output_tokens."""

    seconds: float = 300.0
    output_tokens: int = 2000


@dataclass
class Completion:
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    duration_s: float


def count_tokens(messages: list[dict]) -> int:
    return max(1, sum(len(m.get("content", "")) for m in messages) // 4)


def fingerprint(model: str, messages: list[dict], max_tokens: int) -> str:
    blob = json.dumps({"messages": messages, "max_tokens": max_tokens}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


@dataclass
class FakeProvider:
    clock: Clock
    script: list = field(default_factory=list)  # items: Reply, Stall or a ProviderError instance
    default: object = field(default_factory=Reply)
    calls: list = field(default_factory=list)
    usage: list = field(default_factory=list)

    def generation_seconds(self, output_tokens: int) -> float:
        return 0.6 + 0.007 * output_tokens

    def create(self, *, model: str, messages: list[dict], max_tokens: int, timeout: float) -> Completion:
        outcome = self.script.pop(0) if self.script else self.default
        start = self.clock.now()
        fp = fingerprint(model, messages, max_tokens)
        self.calls.append({"model": model, "max_tokens": max_tokens, "timeout": timeout, "at": start, "fingerprint": fp})
        if isinstance(outcome, ProviderError):
            self.clock.sleep(0.2)
            raise outcome
        out = min(outcome.output_tokens, max_tokens)
        inp = count_tokens(messages)
        took = outcome.seconds if isinstance(outcome, Stall) else self.generation_seconds(out)
        # billed whether or not the client is still waiting
        self.usage.append({"at": start, "model": model, "fingerprint": fp, "input_tokens": inp,
                           "output_tokens": out, "duration_s": round(took, 2)})
        if took > timeout:
            self.clock.sleep(timeout)
            raise ProviderTimeout(f"read timeout after {timeout:.1f}s")
        self.clock.sleep(took)
        return Completion(model=model, text=getattr(outcome, "text", ""), input_tokens=inp, output_tokens=out, duration_s=took)
