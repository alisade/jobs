# healthai/w2-c1 - CriteriaService on grpc.aio: concurrent, bounded, deadline-aware

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Mon protobuf and grpc.aio; Tue deadlines, cancellation, status codes)

## Scenario

Kestrel Health Plan's (fictional) PA pipeline has an internal gRPC stage, `CriteriaService`, that checks
the medical-policy criteria for one case against the FHIR store (diagnoses, prior therapies, labs). The
LangGraph criteria agent calls it as a tool and the FastAPI edge calls it for status pages. The first
draft checks criteria one at a time, never times out, and returns `UNKNOWN` errors for bad input. A
case with 30 criteria takes 30 FHIR round trips in series, and one slow FHIR search blocks the whole
call until the client gives up.

## What you have

| Path | What it is |
|---|---|
| `protos/criteria.proto` | the contract (do not change it) |
| `criteria/stubs.py` | generates `gen/criteria_pb2*.py` with grpcio-tools if missing and imports them |
| `criteria/fhir.py` | `FakeFhir`: async `case_exists` and `evaluate`, instrumented (`in_flight`, `max_in_flight`, `cancelled`, `completed`) |
| `criteria/server.py` | the servicer and `serve(fhir, port=0, **kwargs)`; you rewrite the servicer |
| `tests/` | visible tests over a real grpc.aio server and channel on localhost |

## Your task

Implement `CriteriaServicer(fhir, max_concurrency=5, check_timeout_s=2.0)`:

1. Validation with proper status codes via `context.abort`: blank `case_id` or 0 or more than 50
   criteria -> `INVALID_ARGUMENT`; a case the FHIR store does not know -> `NOT_FOUND`.
2. Run the checks concurrently with `asyncio.TaskGroup`, never more than `max_concurrency` FHIR calls in
   flight for this servicer (`asyncio.Semaphore`), results in request order.
3. Each check runs under `asyncio.timeout(budget)`. A timeout is a result (`status: "timeout"`), not a
   failed call. A dependency exception is a result too (`status: "error"`, evidence = exception class
   name). `met`/`not_met` come from `fhir.evaluate`.
4. Respect the caller's deadline: `budget = min(check_timeout_s, context.time_remaining() - 0.05)` when
   the client set one, so the service answers with `timeout` results before the client gives up.
5. Cancellation: when the client cancels or its deadline expires, every in-flight FHIR call must be
   cancelled and every semaphore slot returned (the next request still gets 5-way concurrency).
6. `Health` returns `SERVING`.

## Acceptance criteria (what the grader checks)

- 20 checks at 50 ms each finish in well under a second with exactly 5 in flight at peak.
- Slow checks become `timeout`, failing checks become `error`, order is preserved.
- Correct status codes; 50 criteria allowed, 51 rejected.
- Client deadline and client cancel leave no in-flight work and no leaked slots.

## Run

```
make setup     # shared venv + gen/ stubs
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade healthai/w2-c1
make clean
```
