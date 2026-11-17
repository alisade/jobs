#!/usr/bin/env python3
"""Reproduce the partner sync against YOUR code: seed a temp SQLite db, walk GET /v1/contacts, compare."""

from __future__ import annotations

import asyncio
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import httpx  # noqa: E402

from contacts_api.db import create_schema, make_engine  # noqa: E402
from contacts_api.main import create_app  # noqa: E402
from contacts_api.seed import make_rows, seed  # noqa: E402

TENANT = "app-partner-portal"


async def main(limit: int) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = make_engine(f"sqlite+aiosqlite:///{tmp}/contacts.db")
        await create_schema(engine)
        rows = make_rows(TENANT, 1931, 500)
        await seed(engine, rows)
        app = create_app(engine)
        seen, cursor, pages = [], None, 0
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://svc") as c:
            while True:
                params = {"limit": limit} | ({"cursor": cursor} if cursor else {})
                r = await c.get("/v1/contacts", params=params, headers={"X-Tenant-Id": TENANT})
                r.raise_for_status()
                body = r.json()
                pages += 1
                seen += [x["id"] for x in body["data"]]
                cursor = body["next_cursor"]
                if not cursor:
                    break
        await engine.dispose()
    print(f"pages={pages} received={len(seen)} unique={len(set(seen))} expected={len(rows)} "
          f"missing={len({r['id'] for r in rows} - set(seen))} duplicates={len(seen) - len(set(seen))}")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 100))
