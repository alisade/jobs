# javaai/w2-c1 - Streaming tutor chat: SSE parsing, cancellation and an answer-leak guard

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Tue: signals and RxJS; Wed: HttpClient and streamed responses; Thu: testing services); week 4 (the tutor's guardrails)

## Scenario

Kestrel's Angular tutor panel shows the agent's answer as it streams (server-sent events relayed by
the Spring Boot API). The component is thin: it exposes `TutorChatStore.state$` with `toSignal()`
and calls `ask()` from the form, so all logic is framework-free TypeScript you can test with jest.

Bug reports from the pilot:

- answers sometimes lose words or show a broken character (a "?" diamond) in the middle;
- typing a second question while the first is streaming mixes both answers in the panel;
- when the agent is down the spinner spins forever;
- a learner screenshot shows the tutor saying "They make memory cells that remember the antigen"
  while that learner's open quiz question is "What do vaccines leave behind?" (answer: memory cells).
  The backend guard (w4-c1) caught most of these; the panel must not be the weak link.

## What you have

| Path | What it is |
|---|---|
| `src/types.ts` | `TutorEvent`, `ChatState` |
| `src/sse.ts` | `parseSse` (TODO) |
| `src/leakGuard.ts` | `createLeakGuard` (TODO) |
| `src/tutorChat.ts` | `TutorChatStore` (TODO) |
| `tests/helpers.ts` | `sse()`, `bytes()`, `cut()` and a `FakeApi` whose streams you drive by hand |

## Requirements

**parseSse** - chunks can cut events, lines and UTF-8 characters anywhere: decode as a stream
and keep the unfinished tail; accept `\n` and `\r\n`; ignore comment lines (`: keep-alive`); join
multiple `data:` lines with `\n`; drop an event that was not terminated when the body ends.

**createLeakGuard(secrets)** - `push(text)` returns what is safe to show now, `flush()` the rest.
Every case-insensitive occurrence of a secret becomes `[hint withheld]`, even when it straddles
tokens; never show a prefix of a secret before you know it is not one; lose no other text;
`leaked` reports whether anything was replaced.

**TutorChatStore**
- `ask()` while a stream is in flight cancels it (the old request is unsubscribed) and only the new
  answer reaches the state.
- Tokens go through the leak guard; `done` flushes it and sets `status: "done"`; `withheld` set
  when the guard replaced something.
- Citations kept in arrival order without duplicates.
- An `error` event or a transport error: `status: "error"` with the message; the next `ask()` works.
- No first event within `firstTokenTimeoutMs`: `status: "error"`, `error: "timeout"`, request
  cancelled. A stream that has started is never timed out.

## Acceptance criteria (what the grader checks)

- Hidden jest tests cut the body at every byte offset, one byte per chunk, through multi-byte
  characters, with CRLF, comments, multi-line data and a truncated tail.
- Leak guard across tokens, no false positives, no early prefix.
- Store: cancellation, redaction with flush, citations, both error paths, timeout and no timeout.
- `ANSWER.md`: how this plugs into Angular (HttpClient with `observe: "events"` and
  `reportProgress`, or fetch + ReadableStream; `toSignal`; `takeUntilDestroyed`), and why the
  client guard does not replace the server one.

## How to run

```bash
make setup     # links javaai/_env/node_modules (jest, ts-jest, typescript, rxjs)
make test
# fill in ANSWER.md, then from workbooks/: /grade javaai/w2-c1
make clean
```
