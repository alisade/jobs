# ANSWER: connect/w3-c1 Keep the on-call hotline alive

## Approach

Mapped each incident to the PSTN audio contract: module-scope `state` explains cross-wired
calls (one warm container, many concurrent transactions); `Date.now()` explains the wrong
shift; missing ACTION_FAILED and HANGUP branches explain silence and open legs. Drove fixes
with the SMA stand-in and the recorded fixtures.

## Fix

State machine in TransactionAttributes (COLLECT_ID, MENU, BRIDGE_PRIMARY, BRIDGE_SECONDARY,
BRIDGE_HELPDESK, CONNECTED, ENDING); X-Employee-Id accepted only if six digits; roster from
LEG-A start time; CallerIdNumber = LEG-A To; failover chain; HANGUP hangs up the other leg by
CallId; masked one-line JSON logs. make test and the full simulations pass; replaying an event
returns the same response.

## Trade-offs / what I would do in production

Handler is pure and fast (well inside the 5 s retry window). Alarms on INVALID_LAMBDA_RESPONSE
and Lambda errors. Wave 3: rebuild as a Connect flow (Get customer input, Transfer to phone
number, contact attributes), replace the SIP header with a data dip, port +1 888 555 0177 from
the Chime SDK to Connect by support case after testing on a temporary number.
