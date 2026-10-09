"""A stand-in for the storefront MCP server behind the gateway: answers any JSON-RPC
request with a small result naming the principal the gateway forwarded."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def mcp(request: Request) -> JSONResponse:
    body = await request.json()
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "method": body.get("method"),
                "principal": request.headers.get("x-northwind-principal"),
            },
        }
    )


app = Starlette(routes=[Route("/mcp", mcp, methods=["POST"])])
