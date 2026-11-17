# Reference: genai/x-1

Reference files: `.grading/solution/src/rollout.ts` and `.grading/solution/src/AssistantEntry.tsx`.

- Buckets: FNV-1a over a salted string (`assistant-rollout-v1:` + user id) modulo 100. Salting keeps this
  experiment's cohorts independent of other experiments; changing the salt re-buckets everyone, so
  version it.
- `modeFor`: kill switch first, then `bucket < clamp(percent)`. Monotonic by construction: a user inside
  5% stays inside 25%.
- Flags: `useState(() => flags.get())` plus `subscribe` in an effect that returns the unsubscribe. A
  mode change effect aborts the "on" stream (`stop()`) and the shadow controller, and shows legacy
  results for an already submitted query.
- Shadow: `runShadow` consumes the stream with the vendor parser, measures TTFT and characters, has its
  own budget and AbortController linked to the component's, and returns null when killed so nothing is
  logged for an aborted run.
- Fallback: one effect on `status === "error"`, one timer effect keyed on "waiting for the first token",
  so the timer is cleared as soon as a token arrives. The slow path calls `stop()` so the request (and
  the model call behind it) ends.
- Analytics: every event is built from one `base()` with hash and length; the query text never enters an
  event. Note the limits: a client-side hash of a short query can be guessed; for real privacy hash with
  a server-side secret or send only coarse features.

Production notes: evaluate flags server-side for consistency and to keep the percent private; shadow
traffic costs real tokens (estimate queries per day x tokens x price before turning it on); define stop
criteria per step (fallback rate, TTFT p95, completion, conversion vs control) and who flips the switch.
