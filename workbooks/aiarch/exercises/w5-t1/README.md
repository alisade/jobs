# aiarch/w5-t1 - Tool spans start new traces when tools run in parallel

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 5 (Mon: OTEL GenAI conventions and ADOT; Tue: Transaction Search)

## Symptom

Since the change assistant started calling tools in parallel (release 2.6.0), CloudWatch
Transaction Search shows the agent span and the model call, but each tool call and its tool
server span appear as a separate trace with no parent, and per-conversation latency on the
AgentOps dashboard is too low. Turns with one tool look fine. On-call suspects the propagator
settings or sampling. Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/exported-spans-turn-*.json` | spans exported for a parallel turn and a single-tool turn |
| `incident/otel-env.txt` | OTEL settings of the agent and the tool server |
| `lighthouse/agent.py` | the agent turn loop (edit this) |
| `lighthouse/tools_server.py`, `lighthouse/telemetry.py` | tool server and tracing setup (work as shipped) |

## Your task

1. Find the root cause from the spans and the code; explain why single-tool turns work.
2. Fix `lighthouse/agent.py` so every span of a turn is in one trace, tool spans are children of
   the agent span, server spans are children of their tool span, and tool calls still run in
   parallel.
3. Verify with `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.
   Say whether the propagator or sampling theory holds.

## Acceptance criteria (what the grader checks)

- One root span per turn, correct parent links at both hops, GenAI attributes kept, parallelism
  kept, separate turns stay separate traces.
- `ANSWER.md` names the lost context in worker threads with span evidence.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv (opentelemetry-sdk)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w5-t1
make clean
```

## What to submit

`lighthouse/agent.py` and `ANSWER.md`.
