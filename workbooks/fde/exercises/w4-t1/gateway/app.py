"""The gateway app: auth middleware + one tool route over the storefront executor.

    POST /tools/<name>     Authorization: Bearer <signed claim>     body: tool arguments
    GET  /healthz          no auth

The tool route runs the same ``ShoppingToolExecutor`` the blueprint's storefront MCP
server runs, one executor (and so one provenance record) per customer session.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from commerce_common.skills import SkillRegistry
from shopping_agent import (
    ShoppingAgentConfig,
    ShoppingSessionContext,
    ShoppingSessionState,
    StorefrontBackend,
)
from shopping_agent.executor import ShoppingToolExecutor

from . import identity
from .auth import InvalidClaim, verify_claim
from .sessions import RateLimiter, SessionRecord, SessionStore, digest

log = logging.getLogger("gateway")
audit = logging.getLogger("gateway.audit")

ALLOWED_TOOLS = {
    "search_products",
    "get_product_details",
    "get_cart",
    "add_to_cart",
    "update_cart_item",
    "remove_from_cart",
    "get_orders",
}


class AuthMiddleware:
    """Pure ASGI middleware: verify the claim, rate-limit the customer, bind identity."""

    def __init__(self, app: Any, *, secret: str, limiter: RateLimiter) -> None:
        self.app = app
        self.secret = secret
        self.limiter = limiter

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http" or scope["path"] == "/healthz":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode()
        if not auth.startswith("Bearer "):
            await JSONResponse({"error": "unauthenticated"}, 401)(scope, receive, send)
            return
        try:
            principal = verify_claim(auth[len("Bearer ") :], self.secret)
        except InvalidClaim as exc:
            await JSONResponse({"error": f"invalid claim: {exc}"}, 401)(scope, receive, send)
            return
        handle = identity.bind(principal)
        try:
            if not await self.limiter.hit(principal):
                await JSONResponse({"error": "rate limited"}, 429)(scope, receive, send)
                return
            await self.app(scope, receive, send)
        finally:
            identity.release(handle)


def create_app(
    *,
    secret: str,
    redis_latency_s: float = 0.012,
    session_ttl_s: float = 900.0,
    backend: StorefrontBackend | None = None,
) -> Any:
    if backend is None:
        from retail.api.mock_retail import MockRetail

        backend = MockRetail()
    config = ShoppingAgentConfig()
    sessions = SessionStore(latency_s=redis_latency_s, ttl_s=session_ttl_s)
    executors: dict[str, ShoppingToolExecutor] = {}

    def executor_for(record: SessionRecord) -> ShoppingToolExecutor:
        executor = executors.get(record.session_id)
        if executor is None:
            executor = executors[record.session_id] = ShoppingToolExecutor(
                backend=backend,
                config=config,
                skills=SkillRegistry([]),
                session=ShoppingSessionContext(
                    session_id=record.session_id, user_id=record.principal
                ),
                state=ShoppingSessionState(),
                inline_context=True,
            )
        return executor

    async def call_tool(request: Request) -> JSONResponse:
        name = request.path_params["name"]
        if name not in ALLOWED_TOOLS:
            return JSONResponse({"error": f"unknown tool {name}"}, 404)
        try:
            arguments = await request.json()
        except json.JSONDecodeError:
            arguments = {}
        record = await sessions.load(identity.current_principal())
        outcome = await executor_for(record).execute(name, arguments)
        acting_for = digest(identity.current_principal())
        audit.info(
            "tool=%s customer=%s session=%s blocked=%s error=%s",
            name, acting_for, record.session_id, outcome.blocked, outcome.is_error,
        )
        return JSONResponse(
            {
                "acting_for": acting_for,
                "result_text": outcome.result_text,
                "is_error": outcome.is_error,
                "blocked": outcome.blocked,
            }
        )

    async def healthz(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    inner = Starlette(
        routes=[
            Route("/tools/{name}", call_tool, methods=["POST"]),
            Route("/healthz", healthz, methods=["GET"]),
        ]
    )
    app = AuthMiddleware(inner, secret=secret, limiter=RateLimiter(redis_latency_s))
    app.backend = backend  # type: ignore[attr-defined]  (tests and probes read carts)
    return app


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    values.update({k: v for k, v in os.environ.items() if k.startswith(("GATEWAY_", "REDIS_", "SESSION_"))})
    return values


def main() -> None:
    import uvicorn

    env = load_env(Path(__file__).resolve().parents[1] / "gateway.env")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = create_app(
        secret=env["GATEWAY_SECRET"],
        redis_latency_s=int(env.get("REDIS_LATENCY_MS", "12")) / 1000,
        session_ttl_s=float(env.get("SESSION_CACHE_TTL_S", "900")),
    )
    uvicorn.run(
        app,
        host=env.get("GATEWAY_HOST", "127.0.0.1"),
        port=int(env.get("GATEWAY_PORT", "18410")),
        log_level="warning",
    )


if __name__ == "__main__":
    main()
