# ANSWER: connect/w2-c5 IVR and self-service journey redesign

## Approach

Started from the metrics (where time and callers are lost) and the verbatims, then designed for the top
drivers first and checked every step against the success definitions.

## Fix

Key changes: (1) silent identification by ANI and directory language replaces the ID entry and language
menu; (2) one open question with a DTMF safety net replaces the 7-option tree; (3) push-verified password
reset/unlock and ticket status self-service; (4) QnA answers for VPN how-to; (5) every failure goes to an
agent with context, callbacks above 180 s, outage path after hours; (6) instrumentation and an A/B rollout.
Expected: time to agent ~94 s -> < 45 s; ~9% of calls contained.

## Trade-offs / what I would do in production

Least certain: ANI hit rate, Okta Verify enrollment and Spanish NLU accuracy; validate in a pilot on a
separate DID before the 50/50 split.
