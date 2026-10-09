# fde/ai-t1 - Intermittent 400s from the Messages API after a "latency win" release

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** AI Integration (2: the agent loop; 7: observability), Week 1 (Wed: Messages API tool use, `is_error`)

## Scenario

Lumen Home runs its own shopping assistant on the Messages API: an in-house turn loop
(`agentloop/loop.py`) with four tools in front of internal catalog, inventory, shipping and
order services. Release 2.14.0 went out at 13:40 UTC with three changes (see
`incident/CHANGELOG-2.14.0.txt`). Since then, roughly one turn in thirty ends with "Sorry,
something went wrong", Sentry has a new issue for `BadRequestError: Error code: 400`, and
the on-call channel is split between "we are being rate limited" and "roll it back".

You are the engineer the on-call pulled in. Start from `incident/pager.txt`.

## Your environment

`make setup` replays the 140 recorded turns from the incident window (13:41-14:12 UTC)
through the **current** code and writes the bundle production would have produced:

| Path | What it is |
|---|---|
| `run/logs/agent.jsonl` | the loop's structured INFO+ logs (what Datadog had) |
| `run/sentry/events.jsonl` | one Sentry event per failed turn, with breadcrumbs |
| `run/failing_request.json` | the full request body of the first rejected API call |
| `run/metrics.txt` | turn counts and the error rate for the window |

The replay uses a recorded-response stand-in for `AsyncAnthropic`
(`agentloop/fake_api.py`) that applies the Messages API's request validation and raises the
SDK's real exception types. No API key and no network are involved. Time is compressed
(tool timeout 0.2 s instead of 2 s). Treat `fake_api.py`, `tools.py`, `replay.py` and
`fixtures/` as the outside world: read them, do not change them.

## Task

1. Find the root cause of the 400s, with evidence from the bundle (quote log lines, the
   Sentry message, the request body). Decide what the 429s have to do with it.
2. Fix `agentloop/loop.py` without giving up parallel tool execution.
3. Re-run `make replay` and `make test` to verify, and fill in `ANSWER.md`.

## Acceptance criteria

- Replaying the incident window produces zero HTTP 400s, and every turn returns the
  recorded final answer.
- Every `tool_use` in an assistant message is answered by exactly one `tool_result`, as the
  leading blocks of the next user message, in `tool_use` order.
- A tool that raises, times out, or does not exist yields an `is_error: true` result the
  model can recover from; a turn where every tool fails still finishes.
- Error results do not carry raw exception text (it can include internal hostnames).
- Tool calls in one round still run concurrently; 429 retries still work; task
  cancellation is not converted into a tool error.

## How to run

```bash
make setup     # shared venv + replay the incident window into run/
make replay    # re-run the replay after a change
make test      # visible tests
# from workbooks/: /grade fde/ai-t1
make clean     # removes run/
```

## What to submit

Your fixed `agentloop/loop.py` and `ANSWER.md` (Approach, Root cause with evidence, Fix and
how you verified it, Trade-offs). The root cause and its evidence carry most of the grade.
