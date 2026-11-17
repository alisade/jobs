"""Service-to-service auth: only the catalog API's service account may call the tutor.

Cloud Run with --no-allow-unauthenticated already checks the ID token at the edge; the service checks
again (defence in depth, and because the audience and caller list are application decisions).
"""

from __future__ import annotations

from dataclasses import dataclass


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
    """Return the verified claims, or raise AuthError(401|403, detail).

    TODO(w4-c1): Bearer ID token, RS256 only, verify signature, exp, iss, aud; then email in
    allowed_callers and email_verified true. 401 for anything wrong with the token, 403 for a valid
    token from a caller that is not allowed.
    """
    return {}
