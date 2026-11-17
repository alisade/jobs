# ANSWER: connect/w4-c2 Migration program plan

## Approach

Started from the hard dates (Avaya 2027-03-31, Five9 2027-01-31, Cisco 2027-12-31, blackouts)
and the volume mix, then ordered waves by risk: a small pilot to prove porting, the main desk
before the Avaya renewal, chat and overflow next, the separate Cisco estate last.

## Fix

Five waves plus foundation; coexistence option 3 per number block; a factory with golden call-path
suites and rationalisation; gates for validation, UAT, load and parallel run; a T-minus runbook;
rollback that accepts the port is one-way; a RACI for onshore/offshore/LFG/carrier; hypercare and
recording retention before decommission.

## Trade-offs / what I would do in production

Validate the porting lead times with the carriers and the Five9 extension terms first; the
wave 2 date after the blackout is tight against the Avaya renewal, so the fallback extension
must be negotiated in parallel.
