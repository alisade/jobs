"""Reproduce the incident with time scaled 1:10 (0.1 s here = 1 s in production).

One answer = model call, check_inventory for every product in the answer, second model call.
The API gateway gives up after 30 s (3.0 s here).
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant_tools.catalog_client import FakeCatalog  # noqa: E402
from assistant_tools.inventory_tool import check_inventory  # noqa: E402

SCALE = 0.1
GATEWAY_TIMEOUT = 30 * SCALE
SKUS = [f"KO-SKU-{i:02d}" for i in range(20)]
STORES = ["087", "045"]


async def answer(catalog_latency_prod_s: float, label: str) -> None:
    cat = FakeCatalog(latency_s=catalog_latency_prod_s * SCALE)
    t0 = time.perf_counter()

    async def pipeline():
        await asyncio.sleep(2.1 * SCALE)  # model call 1 (decides to check stock)
        t_tool = time.perf_counter()
        out = await check_inventory(cat, SKUS, STORES, deadline_s=GATEWAY_TIMEOUT - 2.1 * SCALE - 2.3 * SCALE)
        tool_s = time.perf_counter() - t_tool
        await asyncio.sleep(2.3 * SCALE)  # model call 2 (writes the answer)
        return out, tool_s

    try:
        out, tool_s = await asyncio.wait_for(pipeline(), GATEWAY_TIMEOUT)
        total = time.perf_counter() - t0
        unknown = sum(1 for i in out["items"] if i["stock_unknown"])
        print(f"{label:<28} answered in {total / SCALE:5.1f}s (prod)  check_inventory {tool_s / SCALE:5.1f}s"
              f"  catalog calls: single={cat.single_calls} batch={cat.batch_calls}  unknown={unknown}")
    except asyncio.TimeoutError:
        print(f"{label:<28} GATEWAY TIMEOUT after {GATEWAY_TIMEOUT / SCALE:.0f}s (prod)"
              f"  catalog calls so far: single={cat.single_calls} batch={cat.batch_calls}")


async def main():
    await answer(0.18, "normal (catalog p50 180ms)")
    await answer(0.70, "peak (catalog p50 700ms)")


if __name__ == "__main__":
    asyncio.run(main())
