"""A JWKS key cache with refresh on an unknown kid, rate limited.

YOUR WORK GOES HERE (get_key and whatever helpers you need). Requirements in README.md.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

import httpx
from jwt import PyJWK  # noqa: F401  (PyJWK(jwk_dict) -> .key, .key_type, .algorithm_name)


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
        self._clock = clock  # use this, not time.monotonic(), so tests can move time
        self._keys: dict[str, PyJWK] = {}
        self._fetched_at: float | None = None
        self._lock = asyncio.Lock()
        self.fetch_count = 0  # increment once per successful JWKS fetch (tests read it)

    async def get_key(self, kid: str) -> PyJWK:
        """The verification key for ``kid``.

        TODO:
        - fetch the JWKS on first use and again once ttl_s has passed
        - on an unknown kid, refresh once (a rotation), but at most one unknown-kid
          refresh per refresh_cooldown_s (random kids must not stampede the IdP);
          still unknown -> UnknownKid
        - concurrent callers share one in-flight fetch (no thundering herd)
        - a failed refresh keeps serving the last good key set; with no keys at all,
          raise JWKSUnavailable
        - skip keys that are not signing keys or that PyJWK cannot load
        """
        raise NotImplementedError("JWKSCache.get_key")
