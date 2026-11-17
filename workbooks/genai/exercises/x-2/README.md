# genai/x-2 - Human handoff opens the wrong conversation

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 7 add-on (live-round
drills: React state, effects and closures); Week 1 (React components, state and effects)

## Symptom

On Kestrel's "My conversations" page, a customer can switch between assistant conversations and press
"Talk to a person" (or Alt+H). Since release 2026.10.28, contact-center agents often receive a ticket for
a different, older conversation from the same session. The handoff API team sees "duplicate request"
warnings and suspects their new idempotency logic. Someone else suspects the new TanStack Query cache
setting. Read `evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the support case, the ticket, handoff API log, a React DevTools capture, release notes |
| `src/ChatPage.tsx` | the page (conversation switcher, transcript, handoff button, Alt+H) |
| `src/shortcuts.ts`, `src/types.ts` | shortcut registry and types (not the bug) |
| `tests/` | visible tests and fakes, including a repro that fails until you fix it |

## Your task

1. Find the root cause and prove it with the evidence (quote it): which value the page sends, where it
   comes from, why only customers with more than one conversation, and what the API's "duplicate
   request" warnings and the staleTime change do or do not have to do with it.
2. Fix the page so the button and Alt+H always hand off the conversation on screen, including messages
   that arrived after it was opened, without registering the shortcut more than once at a time.
3. Verify with `make test` (the repro must pass).
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix (and verification), Trade-offs / what you
   would do to stop this class of bug.

## Acceptance criteria (what the grader checks)

- After any sequence of switches, the button and Alt+H send the id and transcript on screen, using the
  current `client` prop.
- Exactly one shortcut registration is active at a time; one press or click is one handoff; unmount
  removes the shortcut.
- `ANSWER.md` names the mechanism (what captured what, and when) with evidence and rules out the red
  herrings.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests (the repro fails on the starter)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/x-2
make clean
```
