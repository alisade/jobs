"""Deployment settings for the authenticated storefront MCP server. Given; do not change."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AuthSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # The protected resource: this server's canonical URL. Tokens must name it in `aud`.
    resource: str = "https://mcp.northwind.example/mcp"
    # The one authorization server whose tokens we accept.
    issuer: str = "https://login.northwind.example/"
    jwks_url: str = "https://login.northwind.example/.well-known/jwks.json"
    # Asymmetric algorithms only. Never "none", never an HMAC alg next to a public key.
    algorithms: tuple[str, ...] = ("RS256", "ES256")
    leeway_s: int = Field(default=30, ge=0, le=120)
    required_claims: tuple[str, ...] = ("iss", "aud", "sub", "exp", "iat")
    # JWKS cache: keys are reused for cache_ttl_s; an unknown kid forces a refresh, but at
    # most once per refresh_cooldown_s (an attacker can mint unlimited random kids).
    cache_ttl_s: int = Field(default=600, ge=1)
    refresh_cooldown_s: int = Field(default=30, ge=0)
    # Scopes. Reads need none beyond a valid token; these tools also need a write scope.
    write_tools: dict[str, str] = {"add_to_cart": "cart:write"}
    scopes_supported: tuple[str, ...] = ("cart:read", "cart:write")

    @property
    def resource_metadata_url(self) -> str:
        """RFC 9728 sec. 3: /.well-known/oauth-protected-resource inserted before the path."""
        scheme, rest = self.resource.split("://", 1)
        host, _, path = rest.partition("/")
        suffix = f"/{path}" if path else ""
        return f"{scheme}://{host}/.well-known/oauth-protected-resource{suffix}"
