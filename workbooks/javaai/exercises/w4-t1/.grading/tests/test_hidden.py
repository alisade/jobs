import asyncio
import time
from pathlib import Path

import httpx
import pytest
import yaml

from tutorsvc.app import create_app
from tutorsvc.gemini import BlockingGemini

ROOT = Path(__file__).resolve().parent.parent
LAT = 0.2


def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=10)


async def turns(c, n):
    return await asyncio.gather(*(c.post("/v1/tutor/turn", json={"learnerId": f"l{i}", "message": "Explain osmosis"}) for i in range(n)))


@pytest.mark.asyncio
async def test_concurrent_turns_overlap():
    fake = BlockingGemini(latency_s=LAT)
    async with client(create_app(fake)) as c:
        t0 = time.perf_counter()
        res = await asyncio.wait_for(turns(c, 8), timeout=8)
        wall = time.perf_counter() - t0
    assert all(r.status_code == 200 for r in res)
    assert fake.calls == 8
    assert wall < 4 * LAT, f"8 turns of {LAT}s took {wall:.2f}s: they ran one after another on the event loop"


@pytest.mark.asyncio
async def test_health_check_answers_while_turns_are_in_flight():
    async with client(create_app(BlockingGemini(latency_s=LAT))) as c:
        work = asyncio.ensure_future(turns(c, 4))
        t0 = time.perf_counter()
        await asyncio.sleep(0.02)
        r = await asyncio.wait_for(c.get("/healthz"), timeout=5)
        took = time.perf_counter() - t0
        await asyncio.wait_for(work, timeout=8)
    assert r.status_code == 200
    assert took < 0.02 + LAT / 2, f"/healthz took {took:.2f}s behind model calls; Cloud Run probes would fail the instance"


@pytest.mark.asyncio
async def test_replies_are_unchanged():
    async with client(create_app(BlockingGemini(latency_s=0.01))) as c:
        r = await c.post("/v1/tutor/turn", json={"learnerId": "l1", "message": "What is R0?"})
    assert r.status_code == 200 and "R0" in r.json()["reply"] and "modelMs" in r.json()


def spec():
    return yaml.safe_load((ROOT / "deploy" / "service.yaml").read_text())["spec"]["template"]


def test_request_timeout_covers_long_answers():
    assert int(spec()["spec"]["timeoutSeconds"]) >= 120, "long worked examples take up to 45 s plus queueing; 30 s produces 504s"


def test_concurrency_matches_what_one_instance_can_do():
    cc = int(spec()["spec"]["containerConcurrency"])
    assert 2 <= cc <= 40, f"containerConcurrency {cc}: one worker with a 40-thread pool cannot serve 80 blocking calls; 1 wastes instances"


def test_ingress_stays_internal():
    meta = yaml.safe_load((ROOT / "deploy" / "service.yaml").read_text())["metadata"]
    assert meta["annotations"]["run.googleapis.com/ingress"] == "internal"
