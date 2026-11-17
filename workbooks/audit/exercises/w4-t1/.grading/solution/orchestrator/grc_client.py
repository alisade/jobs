"""GRC issues API client with retries (timeouts with backoff, 429 with Retry-After).

The caller supplies the Idempotency-Key and the client sends the SAME key on every attempt: a
timeout does not tell you whether the server committed, so a retry must be safe to repeat.
"""

from __future__ import annotations

from typing import Callable

from .fakes import GrcTimeout


class GrcUnavailable(Exception):
    """All attempts failed."""


class GrcClient:
    def __init__(self, server, *, sleep: Callable[[float], None], log: Callable[[str], None], max_attempts: int = 2):
        self.server, self.sleep, self.log, self.max_attempts = server, sleep, log, max_attempts

    def create_issue(self, payload: dict, *, idempotency_key: str) -> str:
        if not idempotency_key:
            raise ValueError("idempotency_key is required")
        backoff = 5.0
        headers = {"Idempotency-Key": idempotency_key, "Content-Type": "application/json"}
        for attempt in range(1, self.max_attempts + 1):
            try:
                status, rh, body = self.server.handle("POST", "/api/v2/issues", headers, payload)
            except GrcTimeout as e:
                self.log(f"grc: attempt {attempt}/{self.max_attempts} sample={payload.get('sample_id')} key={idempotency_key} timed out ({e}); backoff {backoff:.0f}s")
                self.sleep(backoff)
                backoff *= 2
                continue
            if status == 429:
                wait = float(rh.get("Retry-After", "1"))
                self.log(f"grc: 429 rate limited ({rh.get('x-request-id')}), honoring Retry-After {wait:.0f}s")
                self.sleep(wait)
                continue
            if status in (200, 201):
                self.log(f"grc: {status} {body['issue_id']} for sample={payload.get('sample_id')} key={idempotency_key} ({rh.get('x-request-id')})")
                return body["issue_id"]
            raise GrcUnavailable(f"GRC returned {status}: {body}")
        raise GrcUnavailable(f"GRC unavailable after {self.max_attempts} attempts")
