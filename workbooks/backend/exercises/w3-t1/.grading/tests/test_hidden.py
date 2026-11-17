import base64
import pathlib
import re

import pytest
from sqlalchemy import insert

from contacts_api import db as dbmod
from contacts_api.seed import IMPORT_TS, make_rows
from testkit import walk

T = "app-partner-portal"


@pytest.mark.parametrize("limit", [1, 7, 100, 499])
async def test_every_row_exactly_once_with_heavy_ties(make_client, limit):
    rows = make_rows(T, 300, 900, seed=limit)
    client, _ = await make_client(rows)
    async with client:
        seen = await walk(client, T, limit)
    assert len(seen) == len(rows) and set(seen) == {r["id"] for r in rows}


async def test_inserts_during_walk_do_not_cause_skips_or_duplicates(make_client):
    rows = make_rows(T, 200, 300)
    client, engine = await make_client(rows)
    extra = make_rows(T, 0, 40, seed=99)
    for i, r in enumerate(extra):
        r["created_at"] = "2026-11-20T00:00:%02d.000000Z" % (i % 60)

    async def on_page(n):
        if n == 3:
            async with engine.begin() as conn:
                await conn.execute(insert(dbmod.contacts), extra)

    async with client:
        seen = await walk(client, T, 50, on_page)
    assert len(seen) == len(set(seen)), "duplicates during a concurrent insert"
    assert {r["id"] for r in rows} <= set(seen), "original rows skipped"


async def test_cursor_is_opaque_urlsafe(make_client):
    client, _ = await make_client(make_rows(T, 0, 30))
    async with client:
        r = await client.get("/v1/contacts", params={"limit": 10}, headers={"X-Tenant-Id": T})
    cur = r.json()["next_cursor"]
    assert re.fullmatch(r"[A-Za-z0-9_-]+=*", cur)
    assert IMPORT_TS not in cur


@pytest.mark.parametrize("bad", ["not-base64!!", base64.urlsafe_b64encode(b"2026-11-02T03:00:00Z").decode(), "e30"])
async def test_tampered_cursor_is_a_400_problem(make_client, bad):
    client, _ = await make_client(make_rows(T, 10, 0))
    async with client:
        r = await client.get("/v1/contacts", params={"cursor": bad}, headers={"X-Tenant-Id": T})
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 400


async def test_limit_bounds(make_client):
    client, _ = await make_client(make_rows(T, 300, 0))
    async with client:
        big = await client.get("/v1/contacts", params={"limit": 5000}, headers={"X-Tenant-Id": T})
        zero = await client.get("/v1/contacts", params={"limit": 0}, headers={"X-Tenant-Id": T})
    assert big.status_code == 200 and len(big.json()["data"]) == 200
    assert zero.status_code == 400


async def test_tenant_isolation_guard(make_client):
    client, _ = await make_client(make_rows(T, 20, 5) + make_rows("bu-emea", 20, 5, seed=3))
    async with client:
        seen = await walk(client, "bu-emea", 7)
    assert len(seen) == 25


def test_index_supports_the_sort():
    cols = [tuple(c.name for c in ix.columns) for ix in dbmod.contacts.indexes]
    assert ("tenant_id", "created_at", "id") in cols


def test_answer_names_the_tie():
    text = pathlib.Path("ANSWER.md").read_text().lower()
    assert re.search(r"\btie|identical created_at|same created_at|duplicate (timestamp|created_at)|not unique", text)
