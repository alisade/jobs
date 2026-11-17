# genai/w1-t1 - Duplicated words in streamed answers after the proxy change

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (streaming a model
response into the UI: SSE, reconnects, Last-Event-ID); Week 3 (streaming end to end behind proxies)

## Symptom

Since 2026-11-04, Kestrel Outfitters customers report that the shopping assistant "stutters": some
answers repeat their first words ("For two people on a weekend trip, the For two people on a weekend
trip, the Ridgeline 2P ..."). It is mostly long answers. The gateway's own transcripts are clean. Two
changes went out that day: web release 2026.11.04 and the edge proxy migration CHG-8812. A frontend
engineer suspects React StrictMode double effects. Read `evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the page, a HAR export, console, edge proxy and gateway logs, release notes, the change record |
| `src/streamClient.ts` | the reconnecting stream client from release 2026.11.04 |
| `src/transcript.ts` | reducer that turns events into the answer text |
| `src/sse.ts` | SSE parser (known good, shared with the panel; not the bug) |
| `tests/gateway.ts` | a fake gateway: serves a recorded answer, drops connections, resumes after Last-Event-ID |
| `tests/stream.test.ts` | visible tests, including a repro that fails until you fix the incident |

## Your task

1. Find the root cause and prove it with the evidence (quote the lines): what the client sends on
   reconnect, what the gateway does with it, why only long answers, why it started on 2026-11-04, and
   whether StrictMode has anything to do with it.
2. Fix the client so a reconnect resumes where it left off, and make the answer robust if a gateway
   replays events anyway (for example an old gateway pod, or a buffer that expired). Keep the "fresh parser
   per connection" behaviour: a half-received event from a dead connection must not leak.
3. Verify with `make test` (the repro must pass) and say what else you would change outside this repo.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix (and verification), Trade-offs / what you
   would do to stop this class of bug.

## Acceptance criteria (what the grader checks)

- After one or more drops (clean close or network error, with or without a half event), the answer text is
  exact, and each reconnect sends the newest event id it has seen.
- If the gateway ignores Last-Event-ID and replays from the start, no words are duplicated.
- The reconnect budget, `done` and abort behave as before.
- `ANSWER.md` names the mechanism precisely with evidence, separates the trigger (proxy idle timeout) from
  the cause, and rules out the red herring.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests (the repro fails on the starter)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w1-t1
make clean
```
