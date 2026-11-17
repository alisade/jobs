"""Access-token verification for the MCP server.

YOUR WORK GOES HERE (TokenVerifier.verify). Requirements in README.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt  # noqa: F401

from .jwks import JWKSCache, JWKSUnavailable, UnknownKid  # noqa: F401
from .settings import AuthSettings


class InvalidToken(Exception):
    """The bearer token is not acceptable. ``str(exc)`` is safe to log, not to return."""


@dataclass(frozen=True)
class Principal:
    sub: str
    scopes: frozenset[str]
    client_id: str | None = None


class TokenVerifier:
    def __init__(self, settings: AuthSettings, jwks: JWKSCache) -> None:
        self._settings = settings
        self._jwks = jwks

    async def verify(self, token: str) -> Principal:
        """A Principal for a good token; InvalidToken for anything else.

        TODO: read the unverified header; pin alg to settings.algorithms and to the key's
        type; look the key up by kid; verify signature, iss, aud (settings.resource),
        exp/nbf with settings.leeway_s, and every claim in settings.required_claims; map
        the space-separated `scope` claim to Principal.scopes.
        """
        raise NotImplementedError("TokenVerifier.verify")
