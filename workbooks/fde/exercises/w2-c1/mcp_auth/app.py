"""The authenticated storefront MCP server: FastMCP over the blueprint's executor and the
retail MockRetail backend, behind BearerAuthMiddleware. Given; you should not need to
change it, but read it: it shows where the verified principal becomes the session.

    uvicorn --factory mcp_auth.app:create_app --port 8300   # needs a real IdP; see tests
"""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from retail.api.mock_retail import MockRetail
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from commerce_common.skills import SkillRegistry
from shopping_agent import ShoppingAgentConfig, ShoppingSessionContext, ShoppingSessionState
from shopping_agent.executor import ShoppingToolExecutor

from .jwks import JWKSCache
from .middleware import BearerAuthMiddleware, protected_resource_metadata
from .settings import AuthSettings
from .verifier import Principal, TokenVerifier


def _principal(ctx: Context) -> Principal:
    request = ctx.request_context.request
    principal = getattr(getattr(request, "state", None), "principal", None)
    if not isinstance(principal, Principal):
        # Unreachable behind the middleware; refuse rather than guess an identity.
        raise PermissionError("no authenticated principal on this request")
    return principal


def build_mcp(backend: Any | None = None) -> FastMCP:
    backend = backend or MockRetail()
    config = ShoppingAgentConfig()
    states: dict[str, ShoppingSessionState] = {}

    def executor_for(principal: Principal) -> ShoppingToolExecutor:
        # The session identity comes from the verified token, never from a tool argument.
        session_id = "mcp-" + hashlib.sha256(principal.sub.encode()).hexdigest()[:24]
        session = ShoppingSessionContext(session_id=session_id, user_id=principal.sub)
        state = states.setdefault(principal.sub, ShoppingSessionState())
        return ShoppingToolExecutor(
            backend=backend, config=config, skills=SkillRegistry([]), session=session,
            state=state, inline_context=True,
        )

    mcp = FastMCP(
        name="northwind-storefront",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*", "localhost:*", "mcp.northwind.example"],
        ),
    )

    @mcp.tool()
    async def whoami(ctx: Context) -> str:
        """The authenticated customer id this connection acts for."""
        return _principal(ctx).sub

    @mcp.tool()
    async def search_products(query: str, ctx: Context) -> str:
        """Search the catalog."""
        out = await executor_for(_principal(ctx)).execute("search_products", {"query": query})
        return out.result_text

    @mcp.tool()
    async def get_cart(ctx: Context) -> str:
        """The authenticated customer's cart."""
        out = await executor_for(_principal(ctx)).execute("get_cart", {})
        return out.result_text

    @mcp.tool()
    async def add_to_cart(product_id: str, ctx: Context, quantity: int = 1) -> str:
        """Add a product returned by search to the cart. Requires scope cart:write."""
        out = await executor_for(_principal(ctx)).execute(
            "add_to_cart", {"product_id": product_id, "quantity": quantity}
        )
        return out.result_text

    return mcp


def build_app(
    settings: AuthSettings,
    verifier: TokenVerifier,
    backend: Any | None = None,
) -> Starlette:
    mcp = build_mcp(backend)
    mcp_app = mcp.streamable_http_app()  # serves POST /mcp
    metadata = protected_resource_metadata(settings)

    async def prm(_: Request) -> JSONResponse:
        return JSONResponse(metadata)

    def lifespan(_app: Starlette):
        return mcp.session_manager.run()

    return Starlette(
        routes=[
            Route("/.well-known/oauth-protected-resource", prm),
            Route("/.well-known/oauth-protected-resource/mcp", prm),
            Mount("/", app=BearerAuthMiddleware(mcp_app, verifier, settings)),
        ],
        lifespan=lifespan,
    )


def create_app() -> Starlette:  # pragma: no cover - for uvicorn --factory
    settings = AuthSettings()
    http = httpx.AsyncClient()
    jwks = JWKSCache(
        settings.jwks_url, http, ttl_s=settings.cache_ttl_s,
        refresh_cooldown_s=settings.refresh_cooldown_s,
    )
    return build_app(settings, TokenVerifier(settings, jwks))
