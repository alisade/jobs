"""In-process harness: the gateway app from gateway.env, an in-memory IdP and upstream
behind httpx.MockTransport, and a clock the test moves. Independent of the processes
make setup started."""

from __future__ import annotations

import json
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from gateway.app import create_app
from gateway.config import load_settings

ENV_KEYS = ("IDP_ISSUER", "IDP_JWKS_URL", "GATEWAY_AUDIENCE", "UPSTREAM_MCP_URL",
            "JWKS_CACHE_TTL", "JWKS_MIN_REFRESH_INTERVAL", "CLOCK_LEEWAY")


def settings_from_file():
    saved = {k: os.environ.pop(k) for k in ENV_KEYS if k in os.environ}
    try:
        return load_settings()
    finally:
        os.environ.update(saved)


class Clock:
    def __init__(self) -> None:
        self.t = 5000.0

    def __call__(self) -> float:
        return self.t


@dataclass
class FakeIdP:
    settings: object
    keys: dict = field(default_factory=dict)
    published: list = field(default_factory=list)
    jwks_fetches: int = 0

    def add(self, kid: str, publish: bool = True) -> None:
        self.keys[kid] = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if publish:
            self.published.append(kid)

    def handler(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == self.settings.jwks_url:
            self.jwks_fetches += 1
            keys = []
            for kid in self.published:
                jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.keys[kid].public_key()))
                jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
                keys.append(jwk)
            return httpx.Response(200, json={"keys": keys})
        if str(request.url) == self.settings.upstream_url:
            body = json.loads(request.content or b"{}")
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": body.get("id"),
                                             "result": {"principal": request.headers.get("x-northwind-principal")}})
        return httpx.Response(404)

    def token(self, kid: str, *, sign_with: str | None = None, sub: str = "cust-1001", **over) -> str:
        now = int(time.time())
        claims = {"iss": self.settings.issuer, "aud": self.settings.audience, "sub": sub,
                  "iat": now, "nbf": now - 5, "exp": now + 900}
        claims.update(over)
        return jwt.encode(claims, self.keys[sign_with or kid], algorithm="RS256", headers={"kid": kid})


@asynccontextmanager
async def gateway(idp: FakeIdP, clock: Clock):
    settings = idp.settings
    http = httpx.AsyncClient(transport=httpx.MockTransport(idp.handler))
    app = create_app(settings, http=http, clock=clock)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://127.0.0.1:18211") as client:
            yield client, app


async def call(client: httpx.AsyncClient, token: str) -> httpx.Response:
    return await client.post("/mcp", headers={"authorization": f"Bearer {token}"},
                             json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
