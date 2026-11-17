import json

import anyio
from mcp import Client

from changemgmt.backends import ChangeStore, Cmdb
from changemgmt.server import build_server

TOKENS = {"lwong": "tok-lwong-7f3a", "mchen": "tok-mchen-91c2", "pnair": "tok-pnair-0b77"}


def session(user="lwong", store=None):
    store = store or ChangeStore()
    return build_server(store, Cmdb(), TOKENS[user]), store


def call(srv, name, args):
    async def go():
        async with Client(srv) as c:
            r = await c.call_tool(name, args)
            text = r.content[0].text if r.content else ""
            try:
                body = json.loads(text)
            except ValueError:
                body = text
            return r.is_error, body
    return anyio.run(go)


def tools(srv):
    async def go():
        async with Client(srv) as c:
            return (await c.list_tools()).tools
    return anyio.run(go)
