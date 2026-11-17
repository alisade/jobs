import pytest

from keystone_mcp.audit import FIELDS, args_digest
from keystone_mcp.identity import InvalidDelegation
from testkit import NOW, call, session, token

FORBIDDEN_ARGS = {"tenant", "tenant_id", "user", "user_id", "on_behalf_of", "agent_id", "scopes"}
EMEA_READER = dict(user="usr-emea-rep-1", tenant="bu-emea", scopes=("crm.read",))


async def test_schemas_take_no_identity_arguments_and_describe_themselves(world):
    async with session(world, token()) as c:
        tools = (await c.list_tools()).tools
    for t in tools:
        assert not FORBIDDEN_ARGS & set(t.input_schema.get("properties", {})), t.name
        assert t.description and len(t.description) >= 40, f"{t.name}: write the description for a model"


async def test_other_tenant_account_is_not_found_and_audited(world):
    async with session(world, token(**EMEA_READER)) as c:
        err, text = await call(c, "get_account_timeline", {"account_id": "acc-amer-001"})
    assert err and "not found" in str(text).lower()
    assert "Renewal pricing" not in str(text)
    last = world.audit.entries()[-1]
    assert last["outcome"] == "not_found" and last["tenant"] == "bu-emea" and last["on_behalf_of"] == "usr-emea-rep-1"


async def test_timeline_limit_bounded_and_content_marked_untrusted(world):
    async with session(world, token()) as c:
        err, _ = await call(c, "get_account_timeline", {"account_id": "acc-amer-001", "limit": 500})
        assert err
        err, data = await call(c, "get_account_timeline", {"account_id": "acc-amer-001"})
    assert not err and data["content_is_untrusted"] is True
    assert world.audit.entries()[0]["outcome"] == "invalid"


async def test_read_only_session_cannot_write_and_denial_is_audited(world):
    async with session(world, token(**EMEA_READER)) as c:
        err, text = await call(c, "log_activity", {"account_id": "acc-emea-001", "type": "call",
                                                   "subject": "Follow-up", "idempotency_key": "key-0000001"})
    assert err and "crm.write" in str(text)
    assert len([a for a in world.store.activities if a.account_id == "acc-emea-001"]) == 1
    assert world.audit.entries()[-1]["outcome"] == "denied"


async def test_log_activity_is_idempotent_per_key(world):
    args = {"account_id": "acc-amer-001", "type": "call", "subject": "Pricing follow-up", "idempotency_key": "k-7f3a2190"}
    async with session(world, token()) as c:
        e1, r1 = await call(c, "log_activity", args)
        e2, r2 = await call(c, "log_activity", args)
        e3, _ = await call(c, "log_activity", {**args, "subject": "Something else"})
    assert not e1 and not e2 and e3
    assert r1["activity_id"] == r2["activity_id"]
    assert sum(1 for a in world.store.activities if a.subject == "Pricing follow-up") == 1


async def test_log_activity_validates_type_and_other_tenant(world):
    async with session(world, token()) as c:
        bad_type, _ = await call(c, "log_activity", {"account_id": "acc-amer-001", "type": "sms",
                                                     "subject": "x", "idempotency_key": "k-00000001"})
        foreign, _ = await call(c, "log_activity", {"account_id": "acc-emea-001", "type": "note",
                                                    "subject": "x", "idempotency_key": "k-00000002"})
    assert bad_type and foreign
    assert not any(a.tenant == "bu-amer" and a.account_id == "acc-emea-001" for a in world.store.activities)


async def test_propose_starts_approval_and_never_assigns(world):
    args = {"lead_id": "lead-amer-101", "owner_id": "usr-amer-rep-2", "reason": "territory"}
    async with session(world, token()) as c:
        e1, r1 = await call(c, "propose_lead_assignment", args)
        e2, r2 = await call(c, "propose_lead_assignment", args)
    assert not e1 and not e2
    assert r1["status"] == "pending_approval" and r1["proposal_id"] == r2["proposal_id"]
    assert world.store.assign_calls == 0 and world.store.leads["lead-amer-101"].owner_id is None
    assert len(world.workflows.started) == 1
    s = world.workflows.started[0]
    assert s["on_behalf_of"] == "usr-amer-rep-1" and s["agent_id"] == "sales-assistant"


@pytest.mark.parametrize("lead,owner", [("lead-emea-201", "usr-amer-rep-2"),
                                        ("lead-amer-101", "usr-emea-rep-1"),
                                        ("lead-amer-101", "usr-amer-gone")])
async def test_propose_rejects_foreign_or_inactive(world, lead, owner):
    async with session(world, token()) as c:
        err, _ = await call(c, "propose_lead_assignment", {"lead_id": lead, "owner_id": owner})
    assert err and not world.workflows.started and world.store.assign_calls == 0


async def test_every_call_audited_with_hash_not_arguments(world):
    async with session(world, token()) as c:
        await call(c, "find_account", {"query": "logistics"})
        await call(c, "get_account_timeline", {"account_id": "acc-emea-001"})
        await call(c, "log_activity", {"account_id": "acc-amer-003", "type": "note",
                                       "subject": "Spoke with Jane Doe, mobile 555-0100", "idempotency_key": "k-aaaaaaaa"})
    entries = world.audit.entries()
    assert [e["tool"] for e in entries] == ["find_account", "get_account_timeline", "log_activity"]
    assert [e["outcome"] for e in entries] == ["ok", "not_found", "ok"]
    for e in entries:
        assert set(FIELDS) <= set(e) and e["agent_id"] == "sales-assistant" and e["on_behalf_of"] == "usr-amer-rep-1"
        assert e["trace_id"]
    assert entries[0]["args_sha256"] == args_digest({"query": "logistics", "limit": 10})
    assert len({e["trace_id"] for e in entries}) == 3
    assert "555-0100" not in str(entries)


@pytest.mark.parametrize("kind", ["bad_signature", "expired", "tampered"])
def test_bad_tokens_are_rejected(world, kind):
    from keystone_mcp.server import build_server
    from testkit import SECRET
    if kind == "bad_signature":
        tok = token(secret=b"someone-else")
    elif kind == "expired":
        tok = token(exp=NOW - 1)
    else:
        good = token(tenant="bu-amer")
        forged = token(tenant="bu-emea", secret=b"x")
        tok = forged.split(".")[0] + "." + good.split(".")[1]
    with pytest.raises(InvalidDelegation):
        build_server(tok, store=world.store, audit=world.audit, workflows=world.workflows, secret=SECRET, clock=lambda: NOW)
