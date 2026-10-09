"""Access-token verification for the MCP server. Reference solution."""

from __future__ import annotations

from dataclasses import dataclass

import jwt

from .jwks import JWKSCache, JWKSUnavailable, UnknownKid
from .settings import AuthSettings

# Which key types each allowed algorithm may be verified with (blocks HS/RS confusion).
_KTY_FOR_ALG = {"RS256": "RSA", "RS384": "RSA", "RS512": "RSA", "PS256": "RSA",
                "ES256": "EC", "ES384": "EC", "EdDSA": "OKP"}


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
        s = self._settings
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise InvalidToken(f"malformed token: {exc}") from exc
        alg = header.get("alg")
        if alg not in s.algorithms:
            raise InvalidToken(f"algorithm not allowed: {alg!r}")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise InvalidToken("missing kid")
        try:
            key = await self._jwks.get_key(kid)
        except UnknownKid as exc:
            raise InvalidToken(f"unknown kid {kid!r}") from exc
        except JWKSUnavailable as exc:
            raise InvalidToken("signing keys unavailable") from exc
        if _KTY_FOR_ALG.get(alg) != key.key_type:
            raise InvalidToken(f"alg {alg} does not match key type {key.key_type}")
        try:
            claims = jwt.decode(
                token,
                key.key,
                algorithms=[alg],
                audience=s.resource,
                issuer=s.issuer,
                leeway=s.leeway_s,
                options={"require": list(s.required_claims)},
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken(f"{type(exc).__name__}: {exc}") from exc
        scope = claims.get("scope", "")
        scopes = frozenset(scope.split()) if isinstance(scope, str) else frozenset()
        return Principal(sub=str(claims["sub"]), scopes=scopes, client_id=claims.get("client_id"))
