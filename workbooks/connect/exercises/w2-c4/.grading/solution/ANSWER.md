# ANSWER: connect/w2-c4 Help desk transformation solution design

## Approach

Read the inputs for the levers (demand mix, AHT, identity friction) before choosing technology; mapped
every requirement to a design element and a measure; sized the peak with Erlang C; planned delivery
backwards from the Avaya renewal decision.

## Fix

DESIGN.md decisions: (1) one Connect Customer instance with Global Resiliency; (2) ServiceNow remains
the agent workspace with embedded CCP and screen pop; (3) identity tiers with push verification, no
knowledge questions; (4) self-service first for password reset and VPN with a 30% containment target;
(5) dedicated-first routing with proficiency criteria, VIP priority and callbacks; (6) async event-driven
integration for incidents and summaries; (7) coexistence by number with batch porting and rollback.

## Trade-offs / what I would do in production

Least certain: containment (validate in the pilot), vendor VDI audio (endpoint tests per site), Okta API
limits during incidents (load test). De-risk with a month-2 spike on push verification and a routing
simulation on real demand before CAB.
