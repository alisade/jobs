"""HalyardRiskClient: async httpx client with a token cache, a budget, and a breaker.

YOUR WORK GOES HERE. README.md has the full contract; the short version:

- Token: OAuth2 client credentials (RFC 6749 sec. 4.4). POST ``token_url`` with form
  ``grant_type=client_credentials&scope=risk.assess`` and HTTP Basic auth
  (client_id:client_secret). The answer is ``{"access_token": ..., "expires_in": <s>}``.
  Reuse it until ``expires_in - token_skew_s`` seconds have passed on ``clock``. Fetch it
  once however many coroutines need it at the same moment.
- Assess: POST ``base_url + /v1/assess`` with the payload as JSON and
  ``Authorization: Bearer <token>``. 200 + JSON object -> return it.
- One ``asyncio.timeout(budget_s)`` covers everything one ``assess`` does.
- 401: drop the token, fetch a fresh one, retry once. A second 401 is RiskUnavailable.
- 5xx / 429 / transport error / unusable body -> RiskUnavailable. Other 4xx -> RiskError.
  Budget exhausted -> RiskTimeout. No httpx exception escapes.
- Breaker: checked before any network call; RiskUnavailable and RiskTimeout count as
  failures; a 200 or a plain RiskError counts as success; a cancelled call releases a
  half-open trial without a verdict.
"""

from __future__ import annotations

import asyncio  # noqa: F401
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from .breaker import CircuitBreaker
from .errors import RiskError, RiskTimeout, RiskUnavailable  # noqa: F401

ASSESS_PATH = "/v1/assess"
TOKEN_SCOPE = "risk.assess"


class HalyardRiskClient:
    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        base_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        budget_s: float = 0.25,
        token_skew_s: float = 30.0,
        breaker: CircuitBreaker | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._http = http
        self._assess_url = base_url.rstrip("/") + ASSESS_PATH
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._budget = budget_s
        self._skew = token_skew_s
        self._clock = clock
        self._breaker = breaker or CircuitBreaker(clock=clock)
        # TODO: token cache state and whatever makes the fetch single-flight

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    async def assess(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        # TODO: breaker check, budget, token, POST, 401 retry, error mapping, breaker verdict
        raise NotImplementedError("HalyardRiskClient.assess")
