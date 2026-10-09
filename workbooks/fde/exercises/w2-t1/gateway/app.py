"""edge-mcp-gateway: bearer-token verification in front of the storefront MCP server.

    uvicorn --factory gateway.app:create_app --port 18211
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
import jwt
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .config import Settings, load_settings
from .jwks_cache import KeyCache, KeyNotFound

log = logging.getLogger("gateway")
ALGORITHMS = ["RS256"]


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _unauthorized(error: str = "invalid_token") -> JSONResponse:
    return JSONResponse(
        {"error": error},
        status_code=401,
        headers={"WWW-Authenticate": f'Bearer error="{error}"'},
    )


def create_app(
    settings: Settings | None = None,
    *,
    http: httpx.AsyncClient | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Starlette:
    settings = settings or load_settings()
    http = http or httpx.AsyncClient()
    cache = KeyCache(
        settings.jwks_url,
        http,
        ttl=settings.jwks_cache_ttl,
        min_refresh_interval=settings.jwks_min_refresh_interval,
        clock=clock,
    )

    async def verify(token: str) -> dict:
        header = jwt.get_unverified_header(token)
        if header.get("alg") not in ALGORITHMS:
            raise jwt.InvalidAlgorithmError(str(header.get("alg")))
        kid = str(header.get("kid"))
        key = await cache.get(kid)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=ALGORITHMS,
            audience=settings.audience,
            issuer=settings.issuer,
            leeway=settings.clock_leeway,
            options={"require": ["exp", "iat", "sub"]},
        )
        skew = claims["iat"] - time.time()
        if skew > 1:
            log.warning(
                "token iat is %.0fs in the future (issuer clock ahead?) sub=%s",
                skew,
                _digest(claims["sub"]),
            )
        return claims

    async def mcp(request: Request) -> Response:
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return _unauthorized("invalid_request")
        token = auth[7:].strip()
        try:
            kid = str(jwt.get_unverified_header(token).get("kid"))
        except jwt.PyJWTError:
            kid = "?"
        try:
            claims = await verify(token)
        except KeyNotFound:
            log.warning("401 invalid_token kid=%s reason=signing key not found", kid)
            return _unauthorized()
        except jwt.PyJWTError as exc:
            log.warning("401 invalid_token kid=%s reason=%s", kid, type(exc).__name__)
            return _unauthorized()
        except httpx.HTTPError as exc:
            log.error("503 jwks fetch failed: %s", type(exc).__name__)
            return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)

        started = time.monotonic()
        upstream = await http.post(
            settings.upstream_url,
            content=await request.body(),
            headers={
                "content-type": request.headers.get("content-type", "application/json"),
                "accept": request.headers.get("accept", "application/json"),
                "x-northwind-principal": claims["sub"],
            },
            timeout=10.0,
        )
        log.info(
            "POST /mcp %d sub=%s kid=%s upstream_ms=%d",
            upstream.status_code,
            _digest(claims["sub"]),
            kid,
            (time.monotonic() - started) * 1000,
        )
        return Response(
            upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type"),
        )

    async def healthz(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    async def debug_jwks(_: Request) -> JSONResponse:
        return JSONResponse(cache.snapshot())

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        await cache.refresh()  # warm the cache so the first request is fast
        yield

    app = Starlette(
        routes=[
            Route("/mcp", mcp, methods=["POST"]),
            Route("/healthz", healthz),
            Route("/debug/jwks", debug_jwks),
        ],
        lifespan=lifespan,
    )
    app.state.key_cache = cache
    return app
