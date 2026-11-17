"""Visible tests: the happy path and the shape of the morning (run them before and after your fix)."""

import grpc

from criteria.fhir import FakeFhir
from criteria.server import serve
from criteria.stubs import pb2, pb2_grpc


def req(n=5):
    return pb2.CheckRequest(case_id="PA-2026-0001", criteria=[f"KHP-MP-0417/{j}" for j in range(n)])


async def test_happy_path():
    server, port = await serve(FakeFhir())
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as ch:
        resp = await pb2_grpc.CriteriaServiceStub(ch).CheckCriteria(req(), timeout=2)
    await server.stop(0)
    assert [r.status for r in resp.results] == ["met"] * 5


async def test_service_recovers_after_a_fhir_latency_spike():
    fhir = FakeFhir(default_delay=0.6)
    server, port = await serve(fhir, check_timeout_s=0.1)
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as ch:
        stub = pb2_grpc.CriteriaServiceStub(ch)
        spike = await stub.CheckCriteria(req(), timeout=2)
        assert [r.status for r in spike.results] == ["timeout"] * 5
        fhir.default_delay = 0.01
        resp = await stub.CheckCriteria(req(), timeout=1)
    await server.stop(0)
    assert [r.status for r in resp.results] == ["met"] * 5
