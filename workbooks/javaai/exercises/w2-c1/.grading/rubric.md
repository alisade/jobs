# Rubric: javaai/w2-c1 Streaming tutor chat: SSE parsing, cancellation and an answer-leak guard
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Streaming correctness | 10 | One TextDecoder with stream: true, a carried-over buffer, CRLF normalisation that survives a CR at a chunk edge, unterminated tail dropped. |
| 3 | RxJS idiom | 10 | switchMap for latest-wins cancellation, timeout({ first }) for time to first event, teardown that unsubscribes the request, no manual subscription leaks. |
| 4 | Guard design | 10 | Hold-back of (longest secret - 1) characters, no prefix leak, no lost text, flush on done and on error; ANSWER.md says the client guard is defence in depth and the server guard (w4-c1) is the real control, because the client can be bypassed. |
| 5 | Production and Angular notes | 10 | HttpClient with observe events / reportProgress or fetch ReadableStream, toSignal in the component, takeUntilDestroyed, aria-live polite region for streamed text, the latency cost of holding back text. |
| 6 | Code quality | 5 | Small pure functions, typed events, no any where avoidable. |
Total: 100
