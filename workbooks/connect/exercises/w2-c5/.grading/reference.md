# Reference: connect/w2-c5

Model answer: `.grading/solution/DESIGN.md`. What great looks like:

- The diagnosis is numeric: ~94 s before queueing, ~37,000 caller-minutes per month; the employee-ID
  step fails first time for 31% and never for 9% and its result is thrown away; six of seven branches
  go to the same skill; the password advice is impossible for a locked-out caller.
- The redesign removes work instead of re-ordering it: identify by ANI and directory language, ask one
  open question with a DTMF safety net, finish the high-volume jobs in self-service with push
  verification, pass everything to the agent.
- Containment is estimated per driver from identification and enrollment rates, totals ~9% of calls
  (~38% of password/unlock and VPN demand), and is defined with a 7-day repeat check.
- Every failure ends at an agent with context; callbacks, after-hours outage path and relay handling
  are explicit.
- The rollout is measured: pilot DID, then a 50/50 split with Distribute by percentage, go/no-go on
  containment, repeats and CSAT.

Common weaknesses: keeping menus and adding NLU on top; containment targets with no definition or
basis; verification that blocks callers who cannot use push; no plan for Spanish or relay callers.
