# connect/ai-t1 - The AI summary is missing and callers hear 8 seconds of silence

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** AI Integration (area 2 the loop, latency); Week 1 (Thu: Lambda in flows, sync 8 s vs async 60 s); Week 5 (Bedrock quotas, cross-region inference, latency budgets)

## Symptom

Before the transfer to an analyst, LFG's inbound flow invokes `lfg-contact-summary`
synchronously (time limit 8 s) to summarize the caller's self-service conversation with Claude
on Amazon Bedrock; the agent panel shows the summary. Since about 14:00 ET on 2026-10-08 roughly
one call in five arrives without a summary, and those callers sit in 8 seconds of silence first.
The Lambda shows zero errors and zero throttles. L2 wants to raise the memory size. Start with
`incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ServiceNow incident and its work notes |
| `incident/flow-logs-2026-10-08.log` | flow log entries for the summarize block |
| `incident/lambda-lfg-contact-summary-2026-10-08.log` | Lambda logs (START/END/REPORT and the app's own log line) |
| `incident/trace-samples.txt` | X-Ray style timelines of sample invocations |
| `incident/metrics-2026-10-08.txt` | Lambda and Bedrock CloudWatch metrics |
| `config/lambda.json` | the deployed function configuration |
| `src/handler.ts`, `src/client.ts` | the function code |

## Your task

1. Find the root cause and prove it: why does Connect take the error branch when the Lambda
   reports no errors, what happens inside a slow invocation, and why did it start at 14:00?
2. Rule the memory theory in or out with evidence.
3. Fix the code and configuration so the function always answers inside the flow's budget:
   a deadline derived from the flow budget and the Lambda's remaining time, a degraded answer
   (`summaryStatus: "DEGRADED"`, `degradedReason`) instead of an exception or a late answer, no
   SDK retry chain that can outlive the budget, a short summary (`maxTokens <= 400`), an empty
   transcript answered without calling Bedrock, and a function timeout no longer than Connect's
   synchronous limit.
4. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups, including when you would switch the block to Connect's
   asynchronous Lambda mode).

## Acceptance criteria (what the grader checks)

The tests drive the real AWS SDK (serialization, retry strategy, backoff, error parsing) through a
fake HTTP handler, with budgets scaled down (1.2 s instead of 6.5 s):
- Healthy, slow, throttling storm, throttle-then-slow, 500, low remaining Lambda time: always a flat
  string map inside the budget, never an exception.
- `maxTokens <= 400` on the request; empty transcript never calls Bedrock.
- `config/lambda.json`: `Timeout <= 8`, `MAX_TOKENS <= 400`.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup     # toolchain + incident bundle
make test
# from workbooks/: /grade connect/ai-t1
make clean
```
