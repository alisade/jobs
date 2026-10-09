"""Test helpers: an in-memory identity provider (keys, JWKS endpoint, token minting) and
the authenticated MCP app wired to it. No network: the JWKS is served by
httpx.MockTransport and the MCP app runs in-process over httpx.ASGITransport."""

from __future__ import annotations

import base64
import json
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from mcp_auth.app import build_app
from mcp_auth.jwks import JWKSCache
from mcp_auth.settings import AuthSettings
from mcp_auth.verifier import TokenVerifier

SETTINGS = AuthSettings()
BASE = "http://127.0.0.1:8300"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@dataclass
class SigningKey:
    kid: str
    alg: str
    private: Any

    def public_jwk(self) -> dict[str, Any]:
        if self.alg.startswith("RS"):
            jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.private.public_key()))
        else:
            jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(self.private.public_key()))
        jwk.update({"kid": self.kid, "use": "sig", "alg": self.alg})
        return jwk


def rsa_key(kid: str) -> SigningKey:
    return SigningKey(kid, "RS256", rsa.generate_private_key(public_exponent=65537, key_size=2048))


def ec_key(kid: str) -> SigningKey:
    return SigningKey(kid, "ES256", ec.generate_private_key(ec.SECP256R1()))


@dataclass
class IdP:
    """Publishes ``published`` keys at the JWKS URL and counts fetches."""

    keys: dict[str, SigningKey] = field(default_factory=dict)
    published: list[str] = field(default_factory=list)
    fetches: int = 0
    fail: bool = False

    def add(self, key: SigningKey, publish: bool = True) -> SigningKey:
        self.keys[key.kid] = key
        if publish:
            self.published.append(key.kid)
        return key

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL(SETTINGS.jwks_url):
            self.fetches += 1
            if self.fail:
                return httpx.Response(503)
            return httpx.Response(
                200, json={"keys": [self.keys[k].public_jwk() for k in self.published]}
            )
        return httpx.Response(404)

    def http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handler))

    def token(self, kid: str, *, sub: str = "cust-1001", scope: str = "cart:read cart:write",
              drop: tuple[str, ...] = (), headers: dict[str, Any] | None = None,
              **overrides: Any) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": SETTINGS.issuer, "aud": SETTINGS.resource, "sub": sub, "scope": scope,
            "iat": now, "nbf": now, "exp": now + 300, "client_id": "managed-agents",
        }
        claims.update(overrides)
        for name in drop:
            claims.pop(name, None)
        key = self.keys[kid]
        return jwt.encode(claims, key.private, algorithm=key.alg,
                          headers={"kid": kid, **(headers or {})})


def make_verifier(idp: IdP, settings: AuthSettings = SETTINGS, clock=None) -> tuple[TokenVerifier, JWKSCache]:
    kwargs = {"clock": clock} if clock else {}
    cache = JWKSCache(settings.jwks_url, idp.http(), ttl_s=settings.cache_ttl_s,
                      refresh_cooldown_s=settings.refresh_cooldown_s, **kwargs)
    return TokenVerifier(settings, cache), cache


@asynccontextmanager
async def running_app(idp: IdP, settings: AuthSettings = SETTINGS):
    """Yields an httpx client bound to the running ASGI app (lifespan started)."""
    verifier, _ = make_verifier(idp, settings)
    app = build_app(settings, verifier)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=BASE) as c:
            yield c


@asynccontextmanager
async def mcp_session(client: httpx.AsyncClient, token: str):
    """A real MCP client session over streamable HTTP, through the auth middleware."""
    client.headers["Authorization"] = f"Bearer {token}"
    async with streamable_http_client(f"{BASE}/mcp", http_client=client,
                                      terminate_on_close=False) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def mcp_call(name: str, arguments: dict[str, Any], rid: int = 1) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


MCP_HEADERS = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
