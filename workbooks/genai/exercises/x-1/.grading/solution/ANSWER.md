# ANSWER: genai/x-1 Ship the assistant into the existing storefront behind a flag

## Approach

I kept the rules in `rollout.ts` as pure functions (bucket, mode, query hash) and tested them alone. In
the component, each concern sits in its own effect: the flag subscription, a mode change, the error
fallback, and the first-token timer. I tested timing with a controllable stream and a small TTFT budget,
so the tests stay bounded.

## Fix

- `rollout.ts`: a salted FNV-1a bucket (0-99, stable per user), `modeFor` with the kill switch first
  and percent clamped, and `hashQuery` with the allowed-field list.
- `AssistantEntry.tsx`: a live flag subscription with cleanup. A mode-change effect aborts the
  on-mode stream and the shadow run, and shows legacy results when the mode becomes off. Shadow mode uses
  `runShadow` with its own budget and logs only. The error and slow-first-token fallbacks stop the
  request, show the notice and run legacy search. "Show regular results" and the handoff are tracked.
- Every event goes through one `base()`, so no query text or user id can enter it.

## Trade-offs / what I would do in production

- Evaluate flags server-side so the percent and the cohorts are consistent across web and app. Keep the
  client subscription only for the kill switch.
- Shadow mode doubles model calls for those queries. At 200k queries/day and about 2k tokens each that
  is a real cost, so I would sample (for example 10%).
- Stop criteria per step: fallback rate under 2%, TTFT p95 under 2.5 s, completion over 97%, and no
  drop in conversion or search exits against the control cohort. On-call can flip the switch.
- A client-side hash of a short query can be brute-forced. For stronger privacy I would hash with a
  server-side secret, or send only coarse features.
