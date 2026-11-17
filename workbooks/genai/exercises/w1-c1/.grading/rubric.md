# Rubric: genai/w1-c1 Streamed shopping-assistant panel (React + TypeScript)
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Parser and transport correctness | 15 | Full: a real line-buffered state machine (not regex over the whole stream), CR at a chunk end handled, `TextDecoder` with `stream: true` plus final flush, reader cancelled in `finally` when not complete. Partial: passes tests by re-parsing the accumulated buffer each chunk (quadratic) or leaks the connection on early stop. |
| 3 | Hook lifecycle | 15 | Full: one AbortController per run, a run id or equivalent so a stale run cannot write state, functional state updates, unmount cleanup, retry reuses the last prompt, `AbortError` is not an error. Partial: works but relies on effects re-running or on closures that would double-subscribe under StrictMode. |
| 4 | UI and accessibility | 10 | Disclosure, labelled controls, `aria-live="polite"` log, `role="alert"` only for errors, buttons disabled appropriately, product cards from structured events (never parsed out of text). |
| 5 | ANSWER.md | 10 | Full: explains fetch stream vs EventSource (POST body, headers, abort), Last-Event-ID resume vs re-ask, proxy buffering and keepalives, render batching for high token rates, what to measure (time to first token, stop rate, error rate). Partial: generic. |
Total: 100
