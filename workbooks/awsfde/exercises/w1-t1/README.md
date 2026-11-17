# awsfde/w1-t1 - Throttling storm after the resilience release

**Type:** troubleshooting | **Estimate:** 2 hours | **Study plan:** Week 1 (Fri: quotas, throttling and retries; Mon: Converse API errors)

## Symptom

Tidewater Analytics (fictional) shipped release 2026.11.06 of the Tidewater Ask answer service on
Friday: "resilience hardening" after an incident where users saw errors during the Monday 09:00
login wave. On Monday 2026-11-09 the 09:00 peak was the worst on record: between 09:02 and 09:12
about a third of questions failed, p95 latency sat at the 29 s gateway limit, and Bedrock
InvocationThrottles were more than 20 times last Monday's, on only ~20% more traffic. It recovered
by itself at about 09:12. The eng manager wants to know why 20% more traffic produced 3x the
Bedrock calls before anyone asks AWS for a quota increase. Read `evidence/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.txt` | the page and the on-call thread |
| `evidence/release-notes-2026.11.06.md`, `evidence/release-2026.11.06.diff` | what shipped on Friday |
| `evidence/previous_release/` | code and config of release 2026.10.30 (last Monday) |
| `evidence/portal-client.md` | how the web portal reacts to each status code (unchanged for months) |
| `run/dashboard.txt` | per-minute panel for both Mondays, 08:50-09:20 (created by `make setup`) |
| `run/logs/<day>/requests.log` | one JSON line per API request with per-attempt detail `[t, app_attempt, sdk_attempt, result]` |
| `answer_svc/` | this checkout: the code running in prod now |
| `config/release.json` | prod settings (model, timeouts, reserved concurrency) |
| `replay/` | the replay: traffic traces, a Bedrock quota token bucket, an emulation of the SDK retry layer from the real botocore client config, API Gateway and Lambda limits. Treat it as the environment, not the suspect. |

## Your task

1. Find the root cause. Prove it with evidence from the logs and the code: how many Bedrock calls
   can one user request make in each release, where each one comes from, and why the storm
   outlived the 40-second login wave.
2. Decide whether the reserved concurrency change and the quota are part of the cause, and say why.
3. Fix it in `answer_svc/` (do not change `replay/` or `evidence/`):
   - Bedrock retries live in **one** layer, at most **4** attempts per request in total.
   - Backoff is exponential with full jitter and a capped delay.
   - `ValidationException` and `AccessDeniedException` are never retried.
   - When the retry budget is exhausted on throttling, return a degraded answer the portal
     understands instead of an internal error (see `evidence/portal-client.md`).
4. Verify: `make test` and `make replay`.
5. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you verified
   it), Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- At most 4 Bedrock calls per request even when every call is throttled; retries in one layer.
- The retrying layer uses capped full jitter; non-retryable errors make exactly one call.
- Throttling ends in a 503 with `Retry-After`, bad input in a 400, access denied in a 500.
- The replay of 2026-11-09 with your code: error rate under 5%, p95 under 8 s, fewer than 1.5
  Bedrock calls per request, with reserved concurrency 150 or 100.
- `ANSWER.md` names the actual mechanism with evidence. A fixed replay with a hand-waved
  explanation does not pass.

## How to run

```bash
make setup     # shared venv + replays both Mondays into run/ (a few seconds)
make test      # visible checks
make replay    # after a fix: replay this checkout on 2026-11-09 and print the summary
# from workbooks/: /grade awsfde/w1-t1
make clean     # removes run/
```

Useful: `grep -c . run/logs/2026-11-09/requests.log`,
`jq -c 'select(.model_calls > 10) | {request_id, status, model_calls}' run/logs/2026-11-09/requests.log | head`,
`python -c "import boto3; from botocore.config import Config; print(boto3.client('bedrock-runtime', region_name='us-east-1', config=Config(retries={'max_attempts': 10})).meta.config.retries)"`.
