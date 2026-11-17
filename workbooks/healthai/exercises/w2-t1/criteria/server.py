"""CriteriaService on grpc.aio (release 2026.10.2)."""

from __future__ import annotations

import asyncio
import logging

import grpc

from .stubs import pb2, pb2_grpc

MAX_CRITERIA = 50
log = logging.getLogger("criteria.server")


class CriteriaServicer(pb2_grpc.CriteriaServiceServicer):
    def __init__(self, fhir, max_concurrency: int = 5, check_timeout_s: float = 2.0):
        self.fhir = fhir
        self.max_concurrency = max_concurrency
        self.sem = asyncio.Semaphore(max_concurrency)
        self.check_timeout_s = check_timeout_s
        self.inflight = 0

    def permits_free(self) -> int:
        return self.sem._value  # exported as criteria_permits_free

    async def _check(self, case_id: str, criterion: str, budget: float) -> "pb2.CriterionResult":
        await self.sem.acquire()
        self.inflight += 1
        try:
            async with asyncio.timeout(budget):
                met, evidence = await self.fhir.evaluate(case_id, criterion)
            self.inflight -= 1
            self.sem.release()
            return pb2.CriterionResult(criterion_id=criterion, status="met" if met else "not_met", evidence=evidence)
        except BaseException as exc:  # one bad criterion must never fail the whole batch (INC-47702)
            self.inflight -= 1
            log.warning("criterion %s for %s failed: %r", criterion, case_id, exc)
            status = "timeout" if isinstance(exc, TimeoutError) else "error"
            return pb2.CriterionResult(criterion_id=criterion, status=status, evidence=type(exc).__name__)

    async def CheckCriteria(self, request, context):
        if not request.case_id.strip():
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "case_id is required")
        if not request.criteria or len(request.criteria) > MAX_CRITERIA:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"between 1 and {MAX_CRITERIA} criteria required")
        if not await self.fhir.case_exists(request.case_id):
            await context.abort(grpc.StatusCode.NOT_FOUND, f"case {request.case_id} not found")
        budget = self.check_timeout_s
        remaining = context.time_remaining()
        if remaining is not None:
            budget = max(0.0, min(budget, remaining - 0.05))
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._check(request.case_id, c, budget)) for c in request.criteria]
        return pb2.CheckResponse(case_id=request.case_id, results=[t.result() for t in tasks])

    async def Health(self, request, context):
        return pb2.HealthResponse(status="SERVING")


async def serve(fhir, port: int = 0, **kwargs):
    server = grpc.aio.server()
    servicer = CriteriaServicer(fhir, **kwargs)
    pb2_grpc.add_CriteriaServiceServicer_to_server(servicer, server)
    bound = server.add_insecure_port(f"127.0.0.1:{port}")
    await server.start()
    server.servicer = servicer  # for metrics and tests
    return server, bound
