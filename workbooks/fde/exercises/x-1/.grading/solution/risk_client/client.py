"""HalyardRiskClient: async httpx client with a token cache, a budget, and a breaker.

Reference solution.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from .breaker import CircuitBreaker
from .errors import RiskError, RiskTimeout, RiskUnavailable

ASSESS_PATH = "/v1/assess"
TOKEN_SCOPE = "risk.assess"


@dataclass(frozen=True)
class _Token:
    value: str
    refresh_at: float  # clock time after which the token is not used any more


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
        self._token: _Token | None = None
        self._token_lock = asyncio.Lock()

    @property
    def breaker(self) -> CircuitBreaker:
        return self._breaker

    # -- tokens -------------------------------------------------------------------

    def _valid(self, token: _Token | None) -> bool:
        return token is not None and self._clock() < token.refresh_at

    async def _get_token(self) -> str:
        if self._valid(self._token):
            return self._token.value  # type: ignore[union-attr]
        async with self._token_lock:
            # Single flight: whoever waited on the lock re-checks before fetching.
            if self._valid(self._token):
                return self._token.value  # type: ignore[union-attr]
            self._token = await self._fetch_token()
            return self._token.value

    async def _fetch_token(self) -> _Token:
        try:
            resp = await self._http.post(
                self._token_url,
                data={"grant_type": "client_credentials", "scope": TOKEN_SCOPE},
                auth=(self._client_id, self._client_secret),
            )
        except httpx.HTTPError as exc:
            raise RiskUnavailable(f"token endpoint unreachable: {type(exc).__name__}") from None
        if resp.status_code != 200:
            raise RiskUnavailable(f"token endpoint answered {resp.status_code}")
        try:
            body = resp.json()
            value = str(body["access_token"])
            expires_in = float(body["expires_in"])
        except (ValueError, KeyError, TypeError):
            raise RiskUnavailable("token endpoint answered an unusable body") from None
        return _Token(value=value, refresh_at=self._clock() + expires_in - self._skew)

    def _invalidate(self, used: str) -> None:
        # Only drop the token this call used; another coroutine may already have replaced it.
        if self._token is not None and self._token.value == used:
            self._token = None

    # -- assess -------------------------------------------------------------------

    async def _post_assess(self, token: str, payload: Mapping[str, Any]) -> httpx.Response:
        try:
            return await self._http.post(
                self._assess_url,
                json=dict(payload),
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError as exc:
            raise RiskUnavailable(f"risk API unreachable: {type(exc).__name__}") from None

    async def _call(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        token = await self._get_token()
        resp = await self._post_assess(token, payload)
        if resp.status_code == 401:
            self._invalidate(token)
            token = await self._get_token()
            resp = await self._post_assess(token, payload)
            if resp.status_code == 401:
                raise RiskUnavailable("risk API rejected a fresh token (401)")
        if resp.status_code == 429 or resp.status_code >= 500:
            raise RiskUnavailable(f"risk API answered {resp.status_code}")
        if resp.status_code != 200:
            raise RiskError(f"risk API refused the request ({resp.status_code})")
        try:
            body = resp.json()
        except ValueError:
            raise RiskUnavailable("risk API answered a body that is not JSON") from None
        if not isinstance(body, dict):
            raise RiskUnavailable("risk API answered a body that is not an object")
        return body

    async def assess(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        self._breaker.before_call()  # CircuitOpen: no network call at all
        try:
            async with asyncio.timeout(self._budget):
                body = await self._call(payload)
        except TimeoutError:
            self._breaker.record_failure()
            raise RiskTimeout(f"risk call exceeded its {self._budget * 1000:.0f} ms budget") from None
        except RiskUnavailable:
            self._breaker.record_failure()
            raise
        except RiskError:
            self._breaker.record_success()  # the API is up; the request was wrong
            raise
        finally:
            self._breaker.release()  # no-op unless a cancelled trial still holds the slot
        self._breaker.record_success()
        return body
