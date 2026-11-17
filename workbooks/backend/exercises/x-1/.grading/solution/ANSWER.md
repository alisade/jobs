# ANSWER: backend/x-1 Timed whiteboard: a self-serve workflow automation service

## Approach

Spent 5 minutes on questions and requirements, 5 on estimates, 10 on API and data model, 10 on the
diagram, 15 on deep dives and curveballs. Opened the curveballs at minute 30 as planned.

## Fix

- I never said how a team deploys its own workers (CI, task queue registration); next time cover the
  onboarding path explicitly because "self-serve" is the core of the prompt.
- The escalation policy is vague: who is the next approver comes from the role hierarchy, which I did
  not model.
- I computed the start rate but did not use it to size workers; say "two workers per team queue is
  plenty, scale on schedule-to-start latency".
- I mentioned audit but not where an auditor reads it.

## Trade-offs / what I would do in production

Least certain: (1) one task queue per team rather than per tenant; validate with a noisy-neighbor test.
(2) Delay topic for over-limit events; validate that ordering per entity still holds when some events
are delayed.
