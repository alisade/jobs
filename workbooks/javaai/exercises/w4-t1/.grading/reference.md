# Reference: javaai/w4-t1

## Root cause

`turn` is `async def` but calls the synchronous `generate_content`. In an async handler FastAPI
runs the code on the event loop, so the blocking network wait freezes the loop: one uvicorn worker
serves one turn at a time (`make load`: 10 turns of 0.5 s take 5 s). Cloud Run happily routes up to
`containerConcurrency: 80` requests to that instance; they queue. The autoscaler adds instances
when in-flight requests approach 80 or CPU approaches its target; with requests waiting on a
blocked loop CPU is 6-9% and in-flight peaks at 71, so it stays at 2-3 instances out of 20. Queue
time plus model time passes `timeoutSeconds: 30`: 504. `/healthz` is on the same blocked loop, so
probes time out too.

## Red herring

One "Starting new instance" with a 3.7 s first request: cold starts cost seconds on a few requests.
min instances 5 adds always-on cost and five more instances that each serve one turn at a time.

## Fix (`.grading/solution/`)

- `tutorsvc/app.py`: `def turn(...)` so Starlette runs it in the threadpool (40 threads by default).
  Alternative: keep `async def` and use the SDK's async client (`client.aio.models.generate_content`)
  or `await asyncio.to_thread(...)`.
- `deploy/service.yaml`: `containerConcurrency: 20` (under the thread pool, and memory per turn),
  `timeoutSeconds: 300` (long worked examples; better still, stream).

## Follow-ups

Stream answers (SSE) so time to first token is what the learner waits for; if streaming continues
after the response starts, consider CPU always allocated. Load test the 09:00 ramp. Alert when
in-flight per instance is high while CPU is low: the signature of a blocked loop.
