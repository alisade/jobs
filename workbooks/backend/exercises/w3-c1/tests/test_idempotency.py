from testkit import hdrs


async def test_create_then_replay(svc):
    client, _app = svc
    body = {"name": "Brightwater Logistics", "domain": "brightwater.io"}
    r1 = await client.post("/v1/accounts", json=body, headers=hdrs("k-1"))
    assert r1.status_code == 201
    r2 = await client.post("/v1/accounts", json=body, headers=hdrs("k-1"))
    assert r2.status_code == 201
    assert r2.json() == r1.json()
    assert r2.headers.get("Idempotent-Replayed") == "true"


async def test_missing_key_is_a_problem(svc):
    client, _app = svc
    r = await client.post("/v1/accounts", json={"name": "No Key Inc"}, headers=hdrs())
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
