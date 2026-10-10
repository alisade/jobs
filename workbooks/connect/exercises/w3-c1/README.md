# connect/w3-c1 - Keep the on-call hotline alive: PSTN audio handler

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Thu: Chime SDK Voice Connector and PSTN audio; Fri: migration telephony)

## Scenario

Before the Connect program started, Larkspur Financial Group built an "IT On-Call Hotline"
(+1 888 555 0177) on the Amazon Chime SDK PSTN audio service: a SIP rule (trigger
`ToPhoneNumber`) sends the call to a SIP media application whose Lambda collects the
caller's employee ID and bridges them to the infrastructure engineer on call. The Avaya
help desk also transfers Sev1 callers to it through the Avaya SBCE, passing the already
verified employee ID in a custom `X-Employee-Id` SIP header.

PSTN audio entered maintenance mode on 2026-09-29 (closed to new customers 2026-10-29;
existing applications stay supported, no new features), and AWS recommends migrating
these workloads to Amazon Connect Customer. The hotline moves to a Connect flow in wave 3
of the migration, roughly five months from now. Until then it must work, and last week it
did not:

- Two engineers were bridged to the wrong callers during the Monday outage (several
  people called at once).
- An engineer at 22:00 was paged for a caller who dialed during the day shift
  ("the roster lookup is off").
- Callers whose engineer did not answer heard silence until they hung up.
- When the caller hung up, the engineer's leg stayed open for 40 minutes (billed).
- Security flagged full employee IDs in CloudWatch Logs.
- Engineers' phones show the caller's personal number, not the hotline, so they ignore the call.

## What you have

| Path | What it is |
|---|---|
| `src/handler.ts` | the inherited Lambda handler (edit this) |
| `src/types.ts` | PSTN audio event/response types (field names per the Chime SDK developer guide) |
| `src/roster.ts`, `config/oncall-roster.json` | on-call roster (works as shipped) |
| `src/prompts.ts` | S3 WAV prompts (keys are fixed) |
| `fixtures/` | recorded invocation events from production (CloudWatch) |
| `tests/sma-sim.ts` | a small SIP media application stand-in that drives your handler through whole calls and checks the response contract (<= 10 actions, string TransactionAttributes, required action parameters, E.164) |

## Requirements

1. No module-level call state: everything about a call lives in `TransactionAttributes`
   (string values; at most 100 keys / 20 KB). A retried invocation must return the same response.
2. `NEW_INBOUND_CALL`: if LEG-A carries a valid six-digit `X-Employee-Id` SIP header (any
   letter case), skip the ID prompt and play the menu; otherwise collect the ID with
   `PlayAudioAndGetDigits` (`^\d{6}$`). Ignore malformed header values.
3. Menu (`^[12]$`): 1 = bridge to the on-call primary (`CallAndBridge`, PSTN endpoint),
   with the "connecting" prompt first; 2 = bridge to the Connect help desk number.
4. The on-call engineer is resolved from the call's `StartTimeInMilliseconds`.
5. `CallerIdNumber` is the hotline number the caller dialed (LEG-A `To`).
6. Bridge failures: primary -> secondary -> "unavailable" prompt and the help desk.
7. ID or menu input fails after its retries: goodbye prompt, then hang up LEG-A.
8. `HANGUP` from LEG-A while LEG-B is connected: hang up LEG-B (by its `CallId`).
   `HANGUP` from LEG-B while LEG-A is connected: "engineer disconnected" prompt, hang up LEG-A.
9. `INVALID_LAMBDA_RESPONSE`: hang up LEG-A. Any other event: a valid empty action list. Never throw.
10. Log one structured line per invocation (transaction id, sequence, event, state, action
    types) with the employee ID masked.

## Acceptance criteria (what the grader checks)

- Whole-call simulations: id prompt, header skip, menu routes, primary/secondary/help desk
  failover, roster by call start time, goodbye on input failure, both hangup directions.
- Recorded fixtures produce the right actions (secondary from TransactionAttributes, LEG-B
  hangup by CallId).
- Concurrency isolation, replay determinism, contract checks on every response.
- No full employee ID in logs; all TransactionAttributes values are strings.
- `ANSWER.md` explains the production failures you fixed and how this handler maps to a
  Connect flow when wave 3 migrates it.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests (whole calls through tests/sma-sim.ts)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w3-c1
make clean
```

Reference: PSTN audio invocation events, actions, transaction attributes and timeouts in the
Amazon Chime SDK developer guide (the service retries an invocation after 5 s and hangs up at
20 s; a response holds at most 10 actions). Migration mapping: "Migrating PSTN audio
workloads to Amazon Connect Customer" in the Chime SDK administrator guide.
