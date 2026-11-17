"""Fire N concurrent turns at the app in-process (no network) and report wall time.

Run: make load
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from tutorsvc.app import create_app  # noqa: E402
from tutorsvc.gemini import BlockingGemini  # noqa: E402


async def main(n: int = 10, latency: float = 0.5) -> None:
    app = create_app(BlockingGemini(latency_s=latency))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        t0 = time.perf_counter()
        async def one(i):
            s = time.perf_counter()
            r = await c.post("/v1/tutor/turn", json={"learnerId": f"l{i}", "message": "Explain osmosis"})
            return r.status_code, time.perf_counter() - s
        res = await asyncio.gather(*(one(i) for i in range(n)))
        wall = time.perf_counter() - t0
    print(f"{n} concurrent turns, model latency {latency:.2f}s each: wall {wall:.2f}s "
          f"({n / wall:.1f} turns/s; fully concurrent would be ~{latency:.2f}s), statuses {sorted(set(s for s, _ in res))}")


if __name__ == "__main__":
    asyncio.run(main())
