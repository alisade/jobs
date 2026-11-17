"""Reproduce the incident locally: concurrent searches plus kubelet-style health probes.

Runs the app in-process over httpx.ASGITransport (one event loop, like one uvicorn worker).
"""

import asyncio
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx  # noqa: E402

from catalog_search.app import app  # noqa: E402


async def probe(c, out):
    # The kubelet sends a probe on its own schedule; latency counts from when the probe was due,
    # including any time it waited for the event loop.
    start = time.perf_counter()
    for i in range(1, 7):
        due = start + 0.5 * i
        await asyncio.sleep(max(0.0, due - time.perf_counter()))
        r = await c.get("/healthz")
        out.append((r.status_code, time.perf_counter() - due))


async def main():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://demo") as c:
        health: list = []
        t0 = time.perf_counter()
        probes = asyncio.create_task(probe(c, health))
        lat = []

        async def one(q):
            s = time.perf_counter()
            r = await c.get("/search", params={"q": q})
            lat.append(time.perf_counter() - s)
            return r.status_code

        codes = await asyncio.gather(*[one(q) for q in ["tent", "pack", "jacket", "stove", "bag"] * 4])
        await probes
        wall = time.perf_counter() - t0
    lat.sort()
    print(f"searches: {len(codes)} status={sorted(set(codes))} wall={wall:.2f}s")
    print(f"search latency p50={statistics.median(lat):.2f}s p95={lat[int(0.95 * (len(lat) - 1))]:.2f}s max={lat[-1]:.2f}s")
    print("healthz probes (kubelet timeoutSeconds=1):")
    for code, dt in health:
        flag = "  <-- would fail the probe" if dt > 1.0 else ""
        print(f"  {code} {dt:.2f}s{flag}")


if __name__ == "__main__":
    asyncio.run(main())
