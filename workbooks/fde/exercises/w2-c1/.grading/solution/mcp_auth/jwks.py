"""A JWKS key cache with refresh on an unknown kid, rate limited. Reference solution."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

import httpx
from jwt import PyJWK


class JWKSUnavailable(Exception):
    """The JWKS endpoint could not be fetched or parsed."""


class UnknownKid(Exception):
    """No key with this kid, even after the refresh the cooldown allows."""


class JWKSCache:
    def __init__(
        self,
        url: str,
        http: httpx.AsyncClient,
        *,
        ttl_s: float = 600,
        refresh_cooldown_s: float = 30,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = url
        self._http = http
        self._ttl = ttl_s
        self._cooldown = refresh_cooldown_s
        self._clock = clock
        self._keys: dict[str, PyJWK] = {}
        self._fetched_at: float | None = None
        self._kid_refresh_at: float | None = None  # last refresh an unknown kid triggered
        self._lock = asyncio.Lock()
        self.fetch_count = 0

    async def get_key(self, kid: str) -> PyJWK:
        now = self._clock()
        if self._fetched_at is None or now - self._fetched_at >= self._ttl:
            await self._refresh(force=True)
        key = self._keys.get(kid)
        if key is not None:
            return key
        # Unknown kid: maybe a rotation. Refresh once, unless we refreshed recently.
        await self._refresh(force=False)
        key = self._keys.get(kid)
        if key is None:
            raise UnknownKid(kid)
        return key

    async def _refresh(self, *, force: bool) -> None:
        seen = self._fetched_at
        async with self._lock:
            # Single flight: someone else refreshed while we waited for the lock.
            if self._fetched_at != seen and self._fetched_at is not None:
                return
            now = self._clock()
            if not force:
                if (
                    self._kid_refresh_at is not None
                    and now - self._kid_refresh_at < self._cooldown
                ):
                    return
                self._kid_refresh_at = now
            try:
                response = await self._http.get(self._url, timeout=5.0)
                response.raise_for_status()
                document: dict[str, Any] = response.json()
                keys: dict[str, PyJWK] = {}
                for jwk in document.get("keys", []):
                    if jwk.get("use", "sig") != "sig" or "kid" not in jwk:
                        continue
                    try:
                        keys[jwk["kid"]] = PyJWK(jwk)
                    except Exception:
                        continue  # an unsupported key type does not poison the set
            except (httpx.HTTPError, ValueError) as exc:
                if self._keys:  # keep serving the last good set
                    self._fetched_at = now
                    return
                raise JWKSUnavailable(str(exc)) from exc
            self.fetch_count += 1
            self._keys = keys
            self._fetched_at = now
