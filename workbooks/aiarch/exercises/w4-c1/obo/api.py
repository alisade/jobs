"""The access-requests API's own token check (works as shipped): it accepts only tokens issued
for it, and logs who it acts for."""
from __future__ import annotations

import jwt

AUDIENCE = "https://access.harborpoint.example"


def verify(token: str, jwks: dict, issuer: str) -> dict:
    key = jwt.PyJWKSet.from_dict(jwks).keys[0].key
    claims = jwt.decode(token, key, algorithms=["RS256"], audience=AUDIENCE, issuer=issuer)
    return {"acting_for": claims["sub"], "actor": (claims.get("act") or {}).get("sub"), "scope": claims["scope"]}
