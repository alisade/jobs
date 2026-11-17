# javaai/w4-t1 - The tutor is slow at 09:00 and some answers never arrive

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 4 (Wed: Cloud Run concurrency, CPU allocation, request timeouts; Mon: FastAPI async vs sync)

## Symptom

At the 09:00 cohort start the tutor chat takes 10-25 s and about 6% of turns end in a Cloud Run
504. Gemini latency is unchanged and there are no 429s. L2 saw "Starting new instance" in the logs
and proposes min instances 5 and max instances 60. Platform notes the autoscaler only ran 2-3
instances and CPU was under 10%. Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/` | page, Cloud Run request logs, metrics |
| `deploy/service.yaml` | the Cloud Run service definition |
| `tutorsvc/app.py` | the FastAPI service (one uvicorn worker per instance) |
| `tutorsvc/gemini.py` | stand-in for the synchronous Gemini SDK call (do not change) |
| `tests/load.py` | `make load`: 10 concurrent turns in-process |

## Your task

1. Find the root cause and prove it with the bundle and a local reproduction (`make load`).
2. Explain why Cloud Run did not scale out, and where the 504s come from.
3. Rule the cold-start theory in or out with evidence.
4. Fix the code and `deploy/service.yaml` so that concurrent turns on one instance overlap, the
   health check answers while turns are in flight, concurrency matches what one instance can serve,
   and the request timeout covers long answers. Keep ingress internal.
5. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups).

## Acceptance criteria (what the grader checks)

- 8 concurrent turns with a 0.2 s model finish in well under 8 x 0.2 s; `/healthz` answers quickly
  during load; replies unchanged.
- `timeoutSeconds >= 120`; `containerConcurrency` between 2 and 40; ingress still internal.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup
make load      # before and after your fix
make test
# from workbooks/: /grade javaai/w4-t1
make clean
```
