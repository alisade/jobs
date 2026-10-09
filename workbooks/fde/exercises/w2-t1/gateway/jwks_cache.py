"""The gateway's JWKS key cache."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

import httpx
from jwt import PyJWK

log = logging.getLogger("gateway.jwks")


class KeyNotFound(Exception):
    pass


class KeyCache:
    def __init__(
        self,
        url: str,
        http: httpx.AsyncClient,
        *,
        ttl: float,
        min_refresh_interval: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.url = url
        self.http = http
        self.ttl = ttl
        self.min_refresh_interval = min_refresh_interval
        self.clock = clock
        self.keys: dict[str, PyJWK] = {}
        self.last_fetch: float | None = None
        self.fetches = 0
        self._lock = asyncio.Lock()

    async def refresh(self) -> None:
        async with self._lock:
            response = await self.http.get(self.url, timeout=5.0)
            response.raise_for_status()
            keys = {}
            for jwk in response.json().get("keys", []):
                try:
                    keys[jwk["kid"]] = PyJWK(jwk)
                except Exception:
                    log.warning("skipping unusable JWK %s", jwk.get("kid"))
            self.keys = keys
            self.last_fetch = self.clock()
            self.fetches += 1
            log.info("jwks refreshed: kids=%s", sorted(keys))

    async def get(self, kid: str) -> PyJWK:
        now = self.clock()
        if self.last_fetch is None or now - self.last_fetch >= self.ttl:
            await self.refresh()
        key = self.keys.get(kid)
        if key is not None:
            return key
        # Unknown kid: refresh, unless we fetched recently (protects the IdP).
        if self.last_fetch is None or now - self.last_fetch >= self.min_refresh_interval:
            await self.refresh()
            key = self.keys.get(kid)
            if key is not None:
                return key
        else:
            log.debug(
                "kid %s unknown; refresh skipped (last fetch %.0fs ago)",
                kid,
                now - self.last_fetch,
            )
        raise KeyNotFound(kid)

    def snapshot(self) -> dict[str, object]:
        age = None if self.last_fetch is None else round(self.clock() - self.last_fetch, 1)
        return {"kids": sorted(self.keys), "last_fetch_age_s": age, "fetches": self.fetches}
