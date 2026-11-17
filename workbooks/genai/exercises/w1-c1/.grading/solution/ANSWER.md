# ANSWER: genai/w1-c1 Streamed shopping-assistant panel

## Approach

I split the work into four layers and tested each one alone: the SSE parser as a pure class (every split
point of the recordings, one character per chunk, CRLF split across chunks), the transport against a fake
`Response` with a byte reader, then the hook and panel with a controllable stream that the test pushes
chunk by chunk.

## Fix

- `sse.ts`: a line-buffered state machine. It keeps the partial line between chunks, remembers a trailing
  CR, dispatches on a blank line, joins `data:` lines, keeps the last id and ignores comments.
- `openStream.ts`: POST with `Accept: text/event-stream`, `StreamHttpError` for non-2xx and non-stream
  bodies, streaming UTF-8 decode, reader cancelled in `finally` on early exit.
- `useAssistantStream.ts`: an AbortController per run and a run counter so stale runs cannot write state.
  It handles error events, thrown errors mapped to the support macros, end without `done` as connection
  lost, the conversation id, retry with the last prompt, and abort on unmount.
- `AssistantPanel.tsx`: disclosure, Stop, a status line, a polite live region, product cards from
  structured events, an alert with Try again, and the handoff button.

## Trade-offs / what I would do in production

- I used fetch streaming over EventSource because the gateway needs POST, headers and abort.
- I did not add automatic reconnect. Resuming needs server-side buffering by event id; re-asking costs a
  second generation. Either way the client must replace the text, never append a replay.
- I would ask platform to disable proxy buffering on the stream route, and send keepalives more often
  than the shortest idle timeout on the path.
- At high token rates I would batch renders per animation frame.
- I would track time to first token, completion rate, stop rate and error rate by code.
