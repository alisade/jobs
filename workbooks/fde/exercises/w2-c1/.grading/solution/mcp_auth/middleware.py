"""Bearer auth as pure ASGI middleware, plus the RFC 9728 metadata document.
Reference solution."""

from __future__ import annotations

import json
import logging
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .settings import AuthSettings
from .verifier import InvalidToken, Principal, TokenVerifier

logger = logging.getLogger("mcp_auth")

MAX_BODY = 1_000_000


def protected_resource_metadata(settings: AuthSettings) -> dict[str, Any]:
    """RFC 9728 sec. 2: what a client needs to find the authorization server."""
    return {
        "resource": settings.resource,
        "authorization_servers": [settings.issuer],
        "scopes_supported": list(settings.scopes_supported),
        "bearer_methods_supported": ["header"],
    }


def _challenge(settings: AuthSettings, error: str | None = None, scope: str | None = None) -> str:
    parts = []
    if error:
        parts.append(f'error="{error}"')
    if scope:
        parts.append(f'scope="{scope}"')
    parts.append(f'resource_metadata="{settings.resource_metadata_url}"')
    return "Bearer " + ", ".join(parts)


async def _reply(send: Send, status: int, body: dict[str, Any], challenge: str) -> None:
    payload = json.dumps(body).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode()),
                (b"www-authenticate", challenge.encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})


def _tool_calls(body: bytes) -> list[str]:
    """Names of the tools a JSON-RPC message (or batch) calls."""
    try:
        doc = json.loads(body or b"null")
    except ValueError:
        return []
    messages = doc if isinstance(doc, list) else [doc]
    names = []
    for m in messages:
        if isinstance(m, dict) and m.get("method") == "tools/call":
            params = m.get("params") or {}
            if isinstance(params, dict) and isinstance(params.get("name"), str):
                names.append(params["name"])
    return names


class BearerAuthMiddleware:
    def __init__(self, app: ASGIApp, verifier: TokenVerifier, settings: AuthSettings) -> None:
        self.app = app
        self.verifier = verifier
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = headers.get("authorization", "")
        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            await _reply(send, 401, {"error": "unauthorized"}, _challenge(self.settings))
            return
        try:
            principal = await self.verifier.verify(token.strip())
        except InvalidToken as exc:
            logger.info("rejected bearer token: %s", exc)  # reason in the log, not the reply
            await _reply(
                send,
                401,
                {"error": "invalid_token"},
                _challenge(self.settings, "invalid_token"),
            )
            return

        receive = await self._enforce_scopes(scope, receive, send, principal)
        if receive is None:
            return
        scope.setdefault("state", {})["principal"] = principal
        await self.app(scope, receive, send)

    async def _enforce_scopes(
        self, scope: Scope, receive: Receive, send: Send, principal: Principal
    ) -> Receive | None:
        if scope.get("method") != "POST":
            return receive
        # Buffer the body to see which tool is called, then replay it downstream.
        chunks: list[bytes] = []
        size = 0
        more = True
        while more:
            message = await receive()
            if message["type"] != "http.request":
                break
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > MAX_BODY:
                await _reply(send, 413, {"error": "body too large"}, _challenge(self.settings))
                return None
            chunks.append(chunk)
            more = message.get("more_body", False)
        body = b"".join(chunks)
        for name in _tool_calls(body):
            needed = self.settings.write_tools.get(name)
            if needed and needed not in principal.scopes:
                await _reply(
                    send,
                    403,
                    {"error": "insufficient_scope", "scope": needed},
                    _challenge(self.settings, "insufficient_scope", needed),
                )
                return None
        sent = False

        async def replay() -> Message:
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        return replay
