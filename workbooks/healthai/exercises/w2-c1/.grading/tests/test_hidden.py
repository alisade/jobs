"""Hidden tests for healthai/w2-c1 (grpc.aio CriteriaService)."""

import asyncio
import time

import grpc
import pytest

from criteria.fhir import FakeFhir
from criteria.stubs import pb2

CASE = "PA-2026-0001"


def req(case_id, criteria):
    return pb2.CheckRequest(case_id=case_id, criteria=list(criteria))


async def settle(fhir, limit=1.0):
    t0 = time.monotonic()
    while fhir.in_flight and time.monotonic() - t0 < limit:
        await asyncio.sleep(0.02)
    return fhir.in_flight


async def test_concurrency_is_bounded_and_real(start):
    fhir = FakeFhir(default_delay=0.05)
    stub = await start(fhir, max_concurrency=5)
    crit = [f"KHP-MP-0417/{i}" for i in range(20)]
    t0 = time.monotonic()
    resp = await stub.CheckCriteria(req(CASE, crit), timeout=5)
    took = time.monotonic() - t0
    assert len(resp.results) == 20
    assert fhir.max_in_flight == 5, f"max in flight {fhir.max_in_flight}"
    assert took < 0.6, f"took {took:.2f}s; checks are not concurrent"


async def test_order_preserved_with_uneven_latency(start):
    crit = ["A/1", "A/2", "A/3x", "A/4"]
    fhir = FakeFhir(delays={"A/1": 0.15, "A/2": 0.01, "A/3x": 0.08, "A/4": 0.0})
    stub = await start(fhir)
    resp = await stub.CheckCriteria(req(CASE, crit), timeout=5)
    assert [r.criterion_id for r in resp.results] == crit
    assert resp.results[2].status == "not_met"
    assert resp.case_id == CASE


async def test_slow_check_is_a_timeout_result_not_a_failed_call(start):
    fhir = FakeFhir(delays={"B/slow": 3.0})
    stub = await start(fhir, check_timeout_s=0.1)
    t0 = time.monotonic()
    resp = await stub.CheckCriteria(req(CASE, ["B/1", "B/slow", "B/2"]), timeout=5)
    assert time.monotonic() - t0 < 1.0
    assert [r.status for r in resp.results] == ["met", "timeout", "met"]
    assert await settle(fhir) == 0


async def test_dependency_error_is_per_criterion(start):
    fhir = FakeFhir(failing={"C/2"})
    stub = await start(fhir)
    resp = await stub.CheckCriteria(req(CASE, ["C/1", "C/2", "C/3"]), timeout=5)
    assert [r.status for r in resp.results] == ["met", "error", "met"]


@pytest.mark.parametrize("case_id,crit", [("", ["X/1"]), ("  ", ["X/1"]), (CASE, []), (CASE, [f"X/{i}" for i in range(51)])])
async def test_invalid_argument(start, case_id, crit):
    stub = await start(FakeFhir())
    with pytest.raises(grpc.aio.AioRpcError) as ei:
        await stub.CheckCriteria(req(case_id, crit), timeout=5)
    assert ei.value.code() == grpc.StatusCode.INVALID_ARGUMENT


async def test_unknown_case_not_found(start):
    stub = await start(FakeFhir())
    with pytest.raises(grpc.aio.AioRpcError) as ei:
        await stub.CheckCriteria(req("PA-2099-9999", ["X/1"]), timeout=5)
    assert ei.value.code() == grpc.StatusCode.NOT_FOUND


async def test_fifty_criteria_is_allowed(start):
    stub = await start(FakeFhir(default_delay=0.0))
    resp = await stub.CheckCriteria(req(CASE, [f"X/{i}" for i in range(50)]), timeout=5)
    assert len(resp.results) == 50


async def test_client_deadline_cancels_server_work(start):
    fhir = FakeFhir(default_delay=1.5)
    stub = await start(fhir, check_timeout_s=5.0)
    with pytest.raises(grpc.aio.AioRpcError) as ei:
        await stub.CheckCriteria(req(CASE, [f"D/{i}" for i in range(8)]), timeout=0.3)
    assert ei.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED
    assert await settle(fhir) == 0, "server kept working after the deadline"
    assert fhir.completed == 0


async def test_client_cancel_cancels_server_tasks_and_frees_slots(start):
    fhir = FakeFhir(default_delay=1.0)
    stub = await start(fhir, check_timeout_s=5.0, max_concurrency=5)
    call = stub.CheckCriteria(req(CASE, [f"E/{i}" for i in range(10)]), timeout=10)
    await asyncio.sleep(0.2)
    call.cancel()
    with pytest.raises(asyncio.CancelledError):
        await call
    assert await settle(fhir) == 0
    assert fhir.cancelled >= 5
    fhir.default_delay = 0.05
    fhir.max_in_flight = 0
    resp = await stub.CheckCriteria(req(CASE, [f"F/{i}" for i in range(10)]), timeout=5)
    assert [r.status for r in resp.results] == ["met"] * 10
    assert fhir.max_in_flight == 5, "semaphore slots leaked by the cancelled call"


async def test_check_budget_respects_short_client_deadline(start):
    fhir = FakeFhir(delays={"G/slow": 2.0})
    stub = await start(fhir, check_timeout_s=5.0)
    resp_or_err = None
    try:
        resp_or_err = await stub.CheckCriteria(req(CASE, ["G/1", "G/slow"]), timeout=0.6)
    except grpc.aio.AioRpcError as exc:
        resp_or_err = exc
    if isinstance(resp_or_err, grpc.aio.AioRpcError):
        pytest.fail("server should shrink the per-check budget to the client deadline and answer 'timeout'")
    assert [r.status for r in resp_or_err.results] == ["met", "timeout"]


async def test_health(start):
    stub = await start(FakeFhir())
    assert (await stub.Health(pb2.HealthRequest(), timeout=5)).status == "SERVING"
