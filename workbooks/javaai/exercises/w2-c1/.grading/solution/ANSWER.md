# ANSWER: javaai/w2-c1 Streaming tutor chat

## Approach

Wrote a cut-at-every-offset harness first, then made the parser buffer text and decode with a
streaming TextDecoder. Built the guard around a hold-back window, then wired the store with
switchMap and timeout({ first }).

## Fix

parseSse buffers across chunks, normalises CRLF, ignores comments, joins data lines and drops an
unterminated tail. The guard redacts across tokens and holds back maxLen - 1 characters. The store
cancels the previous stream, flushes the guard on done/error, dedupes citations, maps both error
kinds to state and times out only before the first event. 17/17 tests.

## Trade-offs / what I would do in production

In Angular: fetch + ReadableStream (or HttpClient events), toSignal in the component,
takeUntilDestroyed, an aria-live="polite" region. Holding back 11 characters adds a little
latency at the end of the stream. The client guard is defence in depth: the server guard is the
control because a client can be bypassed.
