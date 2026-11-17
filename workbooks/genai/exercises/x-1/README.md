# genai/x-1 - Ship the assistant into the existing storefront behind a flag

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 7 add-on (live-round drills);
Week 5 (integrating GenAI into existing enterprise apps: flags, shadow mode, kill switch, human fallback)

## Scenario

Kestrel Outfitters' web shop has had the same search box since 2023, and merchandising depends on its
results markup. Product wants the shopping assistant behind that box, but the rollout plan from the
review is strict:

1. **shadow** for 2 weeks: real queries also go to the assistant in the background, only to measure
   latency and completion. Customers see nothing new.
2. **on** for a growing percentage of customers (5%, 25%, 50%), always with the regular results one
   click away.
3. A **kill switch** the on-call can flip at any time. It takes effect in open browser tabs, without a
   reload.
4. If the assistant errors, or the first word takes too long, the customer gets the regular results
   and a short notice. No spinner forever.
5. Analytics must not contain what customers typed (it may contain names, addresses, order numbers) or
   their user id.

A spike handles a fixed "off" or "on" flag value. You make it production-ready.

## What you have

| Path | What it is |
|---|---|
| `src/AssistantEntry.tsx` | the search box + assistant (spike) |
| `src/rollout.ts` | flag types, cohort and analytics helpers (stubs) |
| `src/LegacySearch.tsx` | the existing results list (do not change) |
| `src/vendor/` | known-good streaming internals: SSE parser, transport, `useAssistantStream` |
| `tests/` | visible tests and fakes (flag client, search, analytics sink, controllable stream) |

## Requirements

**Flags** (`FlagClient.get()` and `subscribe()`): `{ killSwitch, mode: "off" | "shadow" | "on", percent }`.

- `bucketOf(userId)`: deterministic 0-99 bucket, well spread (about N% of users below N), the same on
  every device and render. `modeFor(userId, flags)`: kill switch means "off" for everyone; a user whose
  bucket is below `percent` gets `flags.mode`; everyone else gets "off". Clamp percent to 0-100.
- The component follows flag changes live (subscribe, and unsubscribe on unmount).

**Modes**

- off: legacy results only; the assistant is never called.
- shadow: legacy results render as today; the same query goes to the assistant in the background; the
  answer is consumed and measured, never rendered.
- on: the assistant answer renders in a `role="log"` region named "Assistant answer", with a "Show
  regular results" button that shows the legacy results without removing the answer, and (when
  `onHandoff` is given) "Talk to a person", which calls `onHandoff(conversationId)`.
- When the mode leaves "on" or "shadow" (kill switch or a flag change), stop that assistant request at
  once (abort its signal); if a query was already submitted and the mode is now "off", show its legacy
  results.

**Fallback (on mode):** an assistant error, or no first token within `ttftBudgetMs` (default 4000),
stops the request, shows the legacy results and a `role="status"` with exactly `FALLBACK_NOTICE`.

**Analytics** (`track(event)`), nothing in "off" mode. Allowed fields only: `name, mode, bucket,
queryHash, queryLength, outcome, ttftMs, answerChars, reason, conversationId`.

| name | when | extra fields |
|---|---|---|
| `assistant_query` | a query is submitted in shadow or on | - |
| `assistant_shadow_result` | the shadow answer finished (not when killed) | `outcome` (done, error, timeout), `ttftMs`, `answerChars` |
| `assistant_fallback` | on mode fell back | `reason` (error, slow) |
| `assistant_handoff` | "Talk to a person" | `conversationId` |

`queryHash = hashQuery(query)` (stable, not reversible by reading it), `queryLength` is the query length.

## Acceptance criteria (what the grader checks)

- Cohorts: stable, 0-99, about the right share, monotonic in percent, kill switch wins, clamping.
- Shadow: legacy rendered, assistant called with the same query, result logged, nothing rendered.
- Kill switch live: assistant region gone, request aborted, legacy results shown; turning it off again
  restores the mode; flag subscription released on unmount.
- Fallback on error and on a slow first token (the request is aborted), none when the token is in time.
- Analytics events use only the allowed fields and never contain the query text or the user id.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/x-1
make clean
```
