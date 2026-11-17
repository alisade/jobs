# healthai/w2-t1 - CriteriaService goes dark after a FHIR latency spike

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Tue deadlines, cancellation, status codes; Wed the Cloud Run contract)

## Scenario

At 09:10 the Healthcare API FHIR store had a four-minute latency spike. At 09:14 Kestrel Health Plan's
(fictional) `criteria-service` on Cloud Run started failing every call with `DEADLINE_EXCEEDED`, and it
stayed down long after the FHIR store recovered. CPU was near zero and the Health RPC kept answering
`SERVING`. A redeploy of the same image fixed it instantly. Read `incident/ticket.md`.

## What you have

| Path | What it is |
|---|---|
| `incident/ticket.md`, `incident/criteria-service.log`, `incident/fhir-latency.csv` | the page and the evidence |
| `criteria/server.py` | the service as deployed (release 2026.10.2) |
| `criteria/fhir.py` | the fake FHIR client used by tests and the repro |
| `scripts/repro.py` | `make repro` replays the morning: normal, spike, normal again |
| `findings.json` | your machine-checked findings |

## Your task

1. `make setup`, read the bundle, run `make repro` and explain each phase's numbers.
2. Find the root cause. Explain why the outage outlived the FHIR spike, why CPU was idle, why Health
   said SERVING, and why a restart fixed it.
3. Fix it in `criteria/server.py` without losing the behaviour INC-47702 asked for (one bad criterion
   must not fail the whole batch). Re-run `make repro` and `make test`.
4. Fill in `findings.json` (`root_cause_file`, `root_cause_function`, the `criteria_permits_free` value
   the log shows after the spike, and the red herring in one sentence) and `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- After timeouts, dependency errors, client deadlines and client cancels, all 5 permits are free again
  and the service answers normally.
- Cancelling a check really cancels it (CancelledError propagates); concurrency is still bounded at 5.
- `findings.json` matches the evidence; `ANSWER.md` explains the mechanism with log lines.

## Run

```
make setup && make repro && make test
# fill in ANSWER.md and findings.json, then from workbooks/ in Claude Code: /grade healthai/w2-t1
make clean
```
