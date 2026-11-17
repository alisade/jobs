"""Service-to-service auth: only the catalog API's service account may call the tutor."""

from __future__ import annotations

from dataclasses import dataclass

import jwt


@dataclass(frozen=True)
class AuthConfig:
    audience: str = "https://tutor-agent-7f3k2q-uc.a.run.app"
    issuer: str = "https://accounts.google.com"
    allowed_callers: frozenset[str] = frozenset({"catalog-api@kestrel-prod.iam.gserviceaccount.com"})


class AuthError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def verify_caller(authorization: str | None, public_key_pem: str, cfg: AuthConfig) -> dict:
    if not authorization:
        raise AuthError(401, "missing bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError(401, "expected a Bearer ID token")
    try:
        claims = jwt.decode(token, public_key_pem, algorithms=["RS256"], audience=cfg.audience, issuer=cfg.issuer,
                            options={"require": ["exp", "iss", "aud", "email"]})
    except jwt.PyJWTError as e:
        raise AuthError(401, f"invalid token: {type(e).__name__}")
    if claims.get("email_verified") is not True:
        raise AuthError(403, "caller email not verified")
    if claims.get("email") not in cfg.allowed_callers:
        raise AuthError(403, "caller is not allowed")
    return claims
