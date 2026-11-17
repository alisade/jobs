"""GRC issues API client with retries (timeouts with backoff, 429 with Retry-After)."""

from __future__ import annotations

import uuid
from typing import Callable

from .fakes import GrcTimeout


class GrcUnavailable(Exception):
    """All attempts failed."""


class GrcClient:
    def __init__(self, server, *, sleep: Callable[[float], None], log: Callable[[str], None], max_attempts: int = 2):
        self.server, self.sleep, self.log, self.max_attempts = server, sleep, log, max_attempts

    def create_issue(self, payload: dict) -> str:
        backoff = 5.0
        for attempt in range(1, self.max_attempts + 1):
            key = str(uuid.uuid4())
            headers = {"Idempotency-Key": key, "Content-Type": "application/json"}
            try:
                status, rh, body = self.server.handle("POST", "/api/v2/issues", headers, payload)
            except GrcTimeout as e:
                self.log(f"grc: attempt {attempt}/{self.max_attempts} sample={payload.get('sample_id')} timed out ({e}); backoff {backoff:.0f}s")
                self.sleep(backoff)
                backoff *= 2
                continue
            if status == 429:
                wait = float(rh.get("Retry-After", "1"))
                self.log(f"grc: 429 rate limited ({rh.get('x-request-id')}), honoring Retry-After {wait:.0f}s")
                self.sleep(wait)
                continue
            if status in (200, 201):
                self.log(f"grc: {status} {body['issue_id']} for sample={payload.get('sample_id')} ({rh.get('x-request-id')})")
                return body["issue_id"]
            raise GrcUnavailable(f"GRC returned {status}: {body}")
        raise GrcUnavailable(f"GRC unavailable after {self.max_attempts} attempts")
