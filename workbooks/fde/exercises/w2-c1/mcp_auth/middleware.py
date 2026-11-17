"""Bearer auth as pure ASGI middleware, plus the RFC 9728 metadata document.

YOUR WORK GOES HERE. Requirements in README.md.
"""

from __future__ import annotations

import logging
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

from .settings import AuthSettings
from .verifier import InvalidToken, Principal, TokenVerifier  # noqa: F401

logger = logging.getLogger("mcp_auth")


def protected_resource_metadata(settings: AuthSettings) -> dict[str, Any]:
    """The RFC 9728 protected resource metadata document app.py serves at
    /.well-known/oauth-protected-resource[/mcp].

    TODO: resource, authorization_servers, scopes_supported, bearer_methods_supported.
    """
    raise NotImplementedError("protected_resource_metadata")


class BearerAuthMiddleware:
    """Wraps the FastMCP streamable-HTTP app.

    TODO in __call__ (HTTP scopes only; pass anything else through):
    - no / non-Bearer Authorization -> 401 + WWW-Authenticate challenge carrying
      resource_metadata="<settings.resource_metadata_url>"
    - token fails verification -> 401 with error="invalid_token" in the challenge; the
      reason goes to the log, never into the response
    - a JSON-RPC tools/call (single or batch) for a tool in settings.write_tools without
      that tool's scope -> 403 with error="insufficient_scope", scope="<needed>"; this
      means reading the request body and replaying it to the wrapped app
    - success: put the Principal at scope["state"]["principal"] (app.py reads it as
      request.state.principal) and call the wrapped app
    """

    def __init__(self, app: ASGIApp, verifier: TokenVerifier, settings: AuthSettings) -> None:
        self.app = app
        self.verifier = verifier
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        raise NotImplementedError("BearerAuthMiddleware.__call__")
