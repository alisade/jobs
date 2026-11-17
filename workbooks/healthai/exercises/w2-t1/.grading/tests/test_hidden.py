"""Hidden tests for healthai/w2-t1: permits are never leaked and cancellation propagates."""

import asyncio
import json
from pathlib import Path

import grpc
import pytest

from criteria.fhir import FakeFhir
from criteria.server import CriteriaServicer, serve
from criteria.stubs import pb2, pb2_grpc

EX = Path(__file__).resolve().parent.parent


def req(n=5, prefix="KHP-MP-0417/"):
    return pb2.CheckRequest(case_id="PA-2026-0001", criteria=[f"{prefix}{j}" for j in range(n)])


async def with_stub(fhir, fn, **kw):
    server, port = await serve(fhir, **kw)
    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as ch:
            return await fn(pb2_grpc.CriteriaServiceStub(ch), server.servicer)
    finally:
        await server.stop(0)


async def settle(fhir, limit=1.0):
    for _ in range(int(limit / 0.02)):
        if not fhir.in_flight:
            break
        await asyncio.sleep(0.02)


async def test_permits_return_after_timeouts():
    fhir = FakeFhir(default_delay=0.5)

    async def fn(stub, svc):
        for _ in range(3):
            await stub.CheckCriteria(req(), timeout=3)
        return svc.permits_free()
    assert await with_stub(fhir, fn, check_timeout_s=0.05) == 5


async def test_permits_return_after_dependency_errors():
    fhir = FakeFhir(failing={f"KHP-MP-0417/{j}" for j in range(5)})

    async def fn(stub, svc):
        r = await stub.CheckCriteria(req(), timeout=3)
        assert [x.status for x in r.results] == ["error"] * 5
        return svc.permits_free()
    assert await with_stub(fhir, fn) == 5


async def test_permits_return_after_client_deadline():
    fhir = FakeFhir(default_delay=1.0)

    async def fn(stub, svc):
        try:
            await stub.CheckCriteria(req(), timeout=0.2)  # timeout results or DEADLINE_EXCEEDED, both fine
        except grpc.aio.AioRpcError:
            pass
        await settle(fhir)
        await asyncio.sleep(0.05)
        return svc.permits_free()
    assert await with_stub(fhir, fn, check_timeout_s=5.0) == 5


async def test_permits_return_after_client_cancel():
    fhir = FakeFhir(default_delay=1.0)

    async def fn(stub, svc):
        call = stub.CheckCriteria(req(10), timeout=5)
        await asyncio.sleep(0.2)
        call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await call
        await settle(fhir)
        await asyncio.sleep(0.05)
        return svc.permits_free()
    assert await with_stub(fhir, fn, check_timeout_s=5.0) == 5
    assert fhir.completed == 0


async def test_cancellation_propagates_out_of_check():
    fhir = FakeFhir(default_delay=1.0)
    svc = CriteriaServicer(fhir, check_timeout_s=5.0)
    task = asyncio.create_task(svc._check("PA-2026-0001", "KHP-MP-0417/1", 5.0))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        async with asyncio.timeout(1):
            await task
    assert task.cancelled(), "_check swallowed CancelledError"
    assert svc.sem._value == 5


async def test_service_serves_after_a_spike_under_load():
    fhir = FakeFhir(default_delay=0.6)

    async def fn(stub, svc):
        await asyncio.gather(*(stub.CheckCriteria(req(), timeout=2) for _ in range(4)))
        fhir.default_delay = 0.01
        out = await asyncio.gather(*(stub.CheckCriteria(req(), timeout=1) for _ in range(10)))
        return [r.status for resp in out for r in resp.results]
    statuses = await with_stub(fhir, fn, check_timeout_s=0.1)
    assert statuses == ["met"] * 50


async def test_concurrency_still_bounded_guard():
    fhir = FakeFhir(default_delay=0.05)

    async def fn(stub, svc):
        await stub.CheckCriteria(req(20), timeout=5)
    await with_stub(fhir, fn)
    assert fhir.max_in_flight == 5


def test_findings():
    f = json.loads((EX / "findings.json").read_text())
    assert f["root_cause_file"].endswith("server.py")
    assert f["root_cause_function"] in ("_check", "CriteriaServicer._check")
    assert f["permits_free_before_fix_after_spike"] == 0
    assert any(w in f["red_herring"].lower() for w in ("fhir", "latency"))
