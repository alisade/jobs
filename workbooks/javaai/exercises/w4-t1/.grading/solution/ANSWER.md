# ANSWER: javaai/w4-t1 The tutor is slow at 09:00

## Approach

Metrics first: 2-3 instances of 20, 71 in-flight requests per instance, CPU 9%, Gemini latency
unchanged. Low CPU with deep queues means the instance is waiting, not working. The app log shows
turns completing back to back every ~2.3 s per instance. Read app.py and reproduced with make load.

## Root cause

The async def handler calls the synchronous Gemini SDK, blocking the event loop: one turn at a time
per instance. Cloud Run keeps routing up to containerConcurrency 80 to it, and the autoscaler never
sees in-flight reach 80 or CPU rise, so it does not scale out. Queued turns exceed timeoutSeconds 30
and return 504; the health probe times out behind the same loop. make load: 10 x 0.5 s took 5.05 s.
Cold starts: one new instance and a 3.7 s first request, not the 25 s p95.

## Fix

Handler changed to def (threadpool), containerConcurrency 20, timeoutSeconds 300. make load now
takes ~0.5 s for 10 turns; health checks answer during load; 7/7 tests.

## Trade-offs / what I would do in production

Move to the async client and stream answers; size concurrency to threads and memory; load test the
ramp; alert on high in-flight with low CPU. No min instances needed for this.
