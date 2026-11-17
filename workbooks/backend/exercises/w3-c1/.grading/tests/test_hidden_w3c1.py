import asyncio
from datetime import timedelta

from sqlalchemy import func, select

from app.models import Account, Contact, IdempotencyKey
from testkit import hdrs

BODY = {"name": "Cobalt Analytics", "domain": "cobalt.io"}


async def count(app, model):
    async with app.state.sessionmaker() as s:
        return await s.scalar(select(func.count()).select_from(model))


async def test_twenty_concurrent_retries_create_one_account(svc):
    client, app = svc
    rs = await asyncio.wait_for(asyncio.gather(*[client.post("/v1/accounts", json=BODY, headers=hdrs("burst-1")) for _ in range(20)]), 30)
    assert await count(app, Account) == 1
    codes = sorted(r.status_code for r in rs)
    assert set(codes) <= {201, 409}, codes
    created = [r.json()["id"] for r in rs if r.status_code == 201]
    assert len(set(created)) == 1
    for r in rs:
        if r.status_code == 409:
            assert r.headers["content-type"].startswith("application/problem+json")
            assert "retry-after" in {k.lower() for k in r.headers}


async def test_retry_after_burst_replays(svc):
    client, app = svc
    await asyncio.wait_for(asyncio.gather(*[client.post("/v1/accounts", json=BODY, headers=hdrs("burst-2")) for _ in range(10)]), 30)
    r = await client.post("/v1/accounts", json=BODY, headers=hdrs("burst-2"))
    assert r.status_code == 201 and r.headers.get("Idempotent-Replayed") == "true"
    assert await count(app, Account) == 1


async def test_in_progress_duplicate_gets_409(svc):
    client, app = svc
    app.state.directory.gate = asyncio.Event()
    first = asyncio.create_task(client.post("/v1/accounts", json=BODY, headers=hdrs("slow-1")))
    await asyncio.sleep(0.2)
    second = await asyncio.wait_for(client.post("/v1/accounts", json=BODY, headers=hdrs("slow-1")), 5)
    assert second.status_code == 409
    assert second.headers["content-type"].startswith("application/problem+json")
    assert int(second.headers["Retry-After"]) >= 1
    app.state.directory.gate.set()
    r1 = await asyncio.wait_for(first, 10)
    assert r1.status_code == 201


async def test_same_key_different_body_is_422(svc):
    client, app = svc
    await client.post("/v1/accounts", json=BODY, headers=hdrs("k-mismatch"))
    r = await client.post("/v1/accounts", json={"name": "Something Else"}, headers=hdrs("k-mismatch"))
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert await count(app, Account) == 1


async def test_body_fingerprint_ignores_key_order_and_whitespace(svc):
    client, app = svc
    r1 = await client.post("/v1/accounts", content=b'{"name": "Cobalt Analytics", "domain": "cobalt.io"}',
                           headers={**hdrs("k-canon"), "Content-Type": "application/json"})
    r2 = await client.post("/v1/accounts", content=b'{"domain":"cobalt.io","name":"Cobalt Analytics"}',
                           headers={**hdrs("k-canon"), "Content-Type": "application/json"})
    assert r1.status_code == 201 and r2.status_code == 201
    assert r2.json() == r1.json()


async def test_same_key_on_another_path_is_422(svc):
    client, app = svc
    r1 = await client.post("/v1/accounts", json=BODY, headers=hdrs("k-path"))
    acct = r1.json()["id"]
    r2 = await client.post(f"/v1/accounts/{acct}/contacts", json={"email": "a@cobalt.io", "full_name": "Ana Cho"},
                           headers=hdrs("k-path"))
    assert r2.status_code == 422


async def test_failure_releases_the_key(svc):
    client, app = svc
    app.state.directory.fail_next = 1
    r1 = await client.post("/v1/accounts", json=BODY, headers=hdrs("k-fail"))
    assert r1.status_code == 500
    assert r1.headers["content-type"].startswith("application/problem+json")
    r2 = await client.post("/v1/accounts", json=BODY, headers=hdrs("k-fail"))
    assert r2.status_code == 201
    assert r2.headers.get("Idempotent-Replayed") is None
    assert await count(app, Account) == 1


async def test_keys_are_scoped_per_tenant(svc):
    client, app = svc
    a = await client.post("/v1/accounts", json=BODY, headers=hdrs("shared-key", tenant="bu-amer"))
    b = await client.post("/v1/accounts", json=BODY, headers=hdrs("shared-key", tenant="bu-emea"))
    assert a.status_code == 201 and b.status_code == 201
    assert a.json()["id"] != b.json()["id"]
    assert b.headers.get("Idempotent-Replayed") is None


async def test_expired_key_is_treated_as_new(svc, clock):
    client, app = svc
    a = await client.post("/v1/accounts", json=BODY, headers=hdrs("k-old"))
    clock.now = clock.now + timedelta(hours=25)
    b = await client.post("/v1/accounts", json={"name": "Reused Later"}, headers=hdrs("k-old"))
    assert b.status_code == 201
    assert b.json()["id"] != a.json()["id"]
    assert await count(app, IdempotencyKey) == 1


async def test_concurrent_contact_creation_once(svc):
    client, app = svc
    acct = (await client.post("/v1/accounts", json=BODY, headers=hdrs("k-acct"))).json()["id"]
    body = {"email": "Dana@Cobalt.io", "full_name": "Dana Whitfield"}
    rs = await asyncio.wait_for(asyncio.gather(*[client.post(f"/v1/accounts/{acct}/contacts", json=body, headers=hdrs("c-1")) for _ in range(10)]), 30)
    assert {r.status_code for r in rs} <= {201, 409}
    assert sum(1 for r in rs if r.status_code == 201) >= 1
    assert await count(app, Contact) == 1
    for r in rs:
        if r.status_code == 409:
            assert r.headers["content-type"].startswith("application/problem+json")


async def test_stored_4xx_outcome_is_replayed(svc):
    client, app = svc
    r1 = await client.post("/v1/accounts/does-not-exist/contacts", json={"email": "x@y.io", "full_name": "X"}, headers=hdrs("k-404"))
    assert r1.status_code == 404
    assert r1.headers["content-type"].startswith("application/problem+json")
    r2 = await client.post("/v1/accounts/does-not-exist/contacts", json={"email": "x@y.io", "full_name": "X"}, headers=hdrs("k-404"))
    assert r2.status_code == 404 and r2.headers.get("Idempotent-Replayed") == "true"


async def test_oversized_key_is_400(svc):
    client, app = svc
    r = await client.post("/v1/accounts", json=BODY, headers=hdrs("x" * 300))
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
