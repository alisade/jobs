"""On-behalf-of token exchange (RFC 8693) for Lighthouse tools.

The agent receives the user's access token (audience lighthouse-gateway). A tool that calls the
access-requests API must present a token for THAT API, carrying the user as subject and the
agent as actor, with no more scope than the user has and the tool needs. The inbound token is
never forwarded (token passthrough is the anti-pattern the MCP security guidance names).
"""
from __future__ import annotations

import time
from typing import Callable

import jwt

EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
ACCESS_TOKEN = "urn:ietf:params:oauth:token-type:access_token"
JWT_TYPE = "urn:ietf:params:oauth:token-type:jwt"
ALLOWED_ALGS = ["RS256"]
LEEWAY = 60


class TokenError(Exception):
    """Inbound or exchanged token rejected."""


class InsufficientScope(TokenError):
    pass


def _key_for(token: str, jwks: dict):
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise TokenError(f"malformed token: {e}") from e
    if header.get("alg") not in ALLOWED_ALGS:
        raise TokenError(f"algorithm {header.get('alg')} not allowed")
    for k in jwks.get("keys", []):
        if k.get("kid") == header.get("kid"):
            return jwt.PyJWK.from_dict(k).key
    raise TokenError(f"unknown signing key {header.get('kid')}")


def _decode(token: str, jwks: dict, *, issuer: str, audience: str, now: float, what: str) -> dict:
    key = _key_for(token, jwks)
    try:
        claims = jwt.decode(token, key, algorithms=ALLOWED_ALGS, audience=audience, issuer=issuer,
                            options={"require": ["exp", "iss", "aud", "sub"], "verify_exp": False, "verify_nbf": False, "verify_iat": False})
    except jwt.PyJWTError as e:
        raise TokenError(f"{what} rejected: {e}") from e
    if claims["exp"] + LEEWAY < now:
        raise TokenError(f"{what} rejected: expired")
    if claims.get("nbf", 0) - LEEWAY > now:
        raise TokenError(f"{what} rejected: not yet valid")
    return claims


def validate_inbound(token: str, jwks: dict, *, issuer: str, audience: str, now: float | None = None) -> dict:
    return _decode(token, jwks, issuer=issuer, audience=audience, now=time.time() if now is None else now,
                   what="inbound token")


def build_exchange_request(subject_token: str, *, audience: str, resource: str | None, scopes: list[str],
                           actor_token: str | None = None) -> dict:
    form = {
        "grant_type": EXCHANGE,
        "subject_token": subject_token,
        "subject_token_type": ACCESS_TOKEN,
        "requested_token_type": ACCESS_TOKEN,
        "audience": audience,
        "scope": " ".join(sorted(scopes)),
    }
    if resource:
        form["resource"] = resource
    if actor_token:
        form["actor_token"] = actor_token
        form["actor_token_type"] = JWT_TYPE
    return form


class OboClient:
    def __init__(self, token_endpoint: Callable[[dict], dict], jwks: dict, issuer: str, targets: dict,
                 inbound_audience: str = "lighthouse-gateway", actor_token: Callable[[], str] | None = None,
                 agent_client_id: str | None = None, clock: Callable[[], float] = time.time):
        self.token_endpoint = token_endpoint
        self.jwks = jwks
        self.issuer = issuer
        self.targets = targets
        self.inbound_audience = inbound_audience
        self.actor_token = actor_token
        self.agent_client_id = agent_client_id
        self.clock = clock
        self._cache: dict[tuple, tuple[str, float]] = {}

    def get_downstream_token(self, inbound_token: str, target: str) -> str:
        if target not in self.targets:
            raise TokenError(f"unknown target {target}")
        cfg = self.targets[target]
        now = self.clock()
        user = validate_inbound(inbound_token, self.jwks, issuer=self.issuer, audience=self.inbound_audience, now=now)
        wanted = sorted(set(user.get("scope", "").split()) & set(cfg["scopes"]))
        if not wanted:
            raise InsufficientScope(f"user {user['sub']} has none of {cfg['scopes']} for {target}")
        key = (user["sub"], target, tuple(wanted))
        hit = self._cache.get(key)
        if hit and hit[1] - LEEWAY > now:
            return hit[0]
        form = build_exchange_request(inbound_token, audience=cfg["audience"], resource=cfg.get("resource"),
                                      scopes=wanted, actor_token=self.actor_token() if self.actor_token else None)
        resp = self.token_endpoint(form)
        if "access_token" not in resp:
            raise TokenError(f"token exchange failed: {resp.get('error')} {resp.get('error_description', '')}".strip())
        if resp.get("issued_token_type") != ACCESS_TOKEN:
            raise TokenError(f"unexpected issued_token_type {resp.get('issued_token_type')}")
        token = resp["access_token"]
        if token == inbound_token:
            raise TokenError("IdP returned the subject token unchanged")
        claims = self._check_issued(token, cfg, user, wanted, now)
        self._cache[key] = (token, float(claims["exp"]))
        return token

    def _check_issued(self, token: str, cfg: dict, user: dict, wanted: list[str], now: float) -> dict:
        claims = _decode(token, self.jwks, issuer=self.issuer, audience=cfg["audience"], now=now, what="exchanged token")
        if claims["sub"] != user["sub"]:
            raise TokenError(f"exchanged token is for {claims['sub']}, not the calling user {user['sub']}")
        extra = set(claims.get("scope", "").split()) - set(wanted)
        if extra:
            raise TokenError(f"exchanged token carries scopes that were not requested: {sorted(extra)}")
        if self.agent_client_id and (claims.get("act") or {}).get("sub") != self.agent_client_id:
            raise TokenError("exchanged token does not name the agent as actor")
        return claims
