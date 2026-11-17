"""CriteriaService on grpc.aio. First draft: sequential, unbounded, no validation (see README)."""

from __future__ import annotations

import asyncio  # noqa: F401  (TaskGroup, Semaphore, timeout)

import grpc

from .stubs import pb2, pb2_grpc

MAX_CRITERIA = 50


class CriteriaServicer(pb2_grpc.CriteriaServiceServicer):
    def __init__(self, fhir, max_concurrency: int = 5, check_timeout_s: float = 2.0):
        self.fhir = fhir
        self.max_concurrency = max_concurrency
        self.check_timeout_s = check_timeout_s

    async def CheckCriteria(self, request, context):
        # TODO: validate input (INVALID_ARGUMENT / NOT_FOUND), run checks concurrently with a TaskGroup,
        # bound concurrency, per-check timeout -> "timeout", dependency errors -> "error", respect the
        # client's deadline, keep request order.
        results = []
        for c in request.criteria:
            met, evidence = await self.fhir.evaluate(request.case_id, c)
            results.append(pb2.CriterionResult(criterion_id=c, status="met" if met else "not_met", evidence=evidence))
        return pb2.CheckResponse(case_id=request.case_id, results=results)

    # TODO: Health RPC


async def serve(fhir, port: int = 0, **kwargs) -> tuple[grpc.aio.Server, int]:
    server = grpc.aio.server()
    pb2_grpc.add_CriteriaServiceServicer_to_server(CriteriaServicer(fhir, **kwargs), server)
    bound = server.add_insecure_port(f"127.0.0.1:{port}")
    await server.start()
    return server, bound
