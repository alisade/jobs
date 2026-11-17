"""Live reproduction: normal traffic, a FHIR latency spike, then normal traffic again.

python scripts/repro.py   (about 10 seconds)
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import grpc  # noqa: E402

from criteria.fhir import FakeFhir  # noqa: E402
from criteria.server import serve  # noqa: E402
from criteria.stubs import pb2, pb2_grpc  # noqa: E402


async def phase(name, stub, servicer, n, deadline):
    ok = err = 0
    lat = []

    async def one(i):
        nonlocal ok, err
        t0 = time.monotonic()
        try:
            await stub.CheckCriteria(pb2.CheckRequest(case_id="PA-2026-0001", criteria=[f"KHP-MP-0417/{j}" for j in range(5)]),
                                     timeout=deadline)
            ok += 1
        except grpc.aio.AioRpcError as exc:
            err += 1
            if err == 1:
                print(f"    first error: {exc.code().name}")
        lat.append(time.monotonic() - t0)

    await asyncio.gather(*(one(i) for i in range(n)))
    print(f"{name:<28} ok={ok:<3} errors={err:<3} p50={statistics.median(lat):.2f}s "
          f"criteria_inflight={servicer.inflight} criteria_permits_free={servicer.permits_free()}")


async def main():
    logging.basicConfig(level=logging.ERROR)
    fhir = FakeFhir(default_delay=0.02)
    server, port = await serve(fhir, check_timeout_s=0.3)
    servicer = server.servicer
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as ch:
        stub = pb2_grpc.CriteriaServiceStub(ch)
        await phase("09:05 normal", stub, servicer, 20, 1.0)
        fhir.default_delay = 1.0
        await phase("09:10 FHIR latency spike", stub, servicer, 6, 1.0)
        fhir.default_delay = 0.02
        await asyncio.sleep(0.5)
        await phase("09:16 FHIR back to normal", stub, servicer, 20, 1.0)
    await server.stop(0)


if __name__ == "__main__":
    asyncio.run(main())
