# Reference: javaai/w2-c1

Files in `.grading/solution/src/`: `sse.ts`, `leakGuard.ts`, `tutorChat.ts`.

- **parseSse**: one `TextDecoder` with `{ stream: true }` so a character cut across chunks is
  completed by the next chunk; a string buffer; normalise CRLF but keep a trailing `\r` for the next
  chunk; split on blank lines; parse fields per the SSE format (`field: value`, one optional space,
  comments start with `:`), join data lines with `\n`; drop the leftover at completion.
- **Leak guard**: keep `pending`; on each push redact the whole pending text, then release everything
  except the last `maxLen - 1` characters (they could still be the start of a secret). Do not cut
  inside an inserted marker. `flush` redacts and releases the rest.
- **Store**: `asks$.pipe(switchMap(run))` gives latest-wins and cancels the old HTTP request through
  teardown; `timeout({ first })` covers only the wait for the first event; errors (event or transport)
  become state, and the outer subscription stays alive for the next ask.

## Angular wiring

```ts
// service: fetch + ReadableStream gives true chunks; HttpClient needs observe: 'events',
// reportProgress: true and responseType: 'text' and gives the accumulated text instead.
readonly state = toSignal(this.store.state$, { requireSync: true });
```
Destroying the component should complete the store (takeUntilDestroyed on the outer pipe).

## Interview angles

- Why mergeMap is wrong here (two answers interleave) and when concatMap or exhaustMap would be right.
- The client guard can be bypassed (dev tools, a different client): the server guard is the control.
