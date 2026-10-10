# connect/w5-c1 - Lex V2 code hook for the help desk bot

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 5 (Mon: Lex V2 at lead depth - code hooks, session state, Connect integration)

## Scenario

LFG's self-service bot `LfgHelpDeskBot` (Lex V2, en_US, alias `prod`) answers the help desk
number and the employee portal chat through the Connect flow block "Get customer input" with
Lex. Containment in the pilot was 9%: the code hook Lambda was a stub that delegated every turn,
so Lex accepted "four four one" as an employee ID, reset the wrong system when callers said "the
SAP thing", and every failure arrived at an analyst with no context. The agent screen pop reads
the handoff contract below from Lex session attributes (`$.Lex.SessionAttributes.*`), so the
flow can route and the analyst does not re-ask anything.

One Lambda serves every intent of the locale (Lex allows one code hook Lambda per alias
locale), routed by intent name and `invocationSource`. Recorded Lex V2 events (messageVersion
1.0, documented schema) are in `tests/fixtures/`; backends are interfaces in `src/deps.ts`.

## Requirements

Implement `createHandler(deps)` and `normalizeEmployeeId` in `src/handler.ts`.

1. **Always** return a valid response: `sessionState` with a `dialogAction`; `ElicitSlot` with
   `slotToElicit` and the intent (with its slots); `Close` with `intent.name` and `intent.state`;
   `ConfirmIntent` with intent, slots and a message; `ElicitIntent` with a message; messages as
   `PlainText`. Session attribute values are strings. Never throw: a backend exception becomes a
   `BACKEND_ERROR` handoff.
2. **Preserve** every incoming session attribute (Connect sends `contactId`, `callerVerified`,
   `channel`, sometimes `employeeId`).
3. **EmployeeId** (ResetPassword, UnlockAccount dialog hook): accept `44129`, `E44129`,
   `E 44129`, `e-44129` (normalize to five digits); validate the format and that the directory
   knows it. Invalid or unknown: clear the slot, count `employeeIdAttempts`, re-elicit with a
   message mentioning "five digit"; on the 2nd failure hand off (`EMPLOYEE_ID_INVALID` or
   `EMPLOYEE_NOT_FOUND`, queue `GeneralSupport`). If Connect already verified the caller
   (`callerVerified=true` and `employeeId` attribute), prefill the slot and do not ask.
4. **SystemName** (ResetPassword): use the slot's `resolvedValues` (custom slot type with
   TopResolution; codes `EMAIL`, `VPN`, `SAP`, `SAP_CONCUR`, `WORKDAY`). Empty: elicit listing the
   systems. Several resolved values: clear and ask "Did you mean SAP or SAP Concur?". None
   resolved: clear and re-elicit listing the systems.
5. **Confirmation**: with both slots good and `confirmationState` None, `ConfirmIntent` naming
   the system but never the full employee ID. `Confirmed`: `Delegate`. `Denied`: clear
   SystemName and re-elicit it. The dialog hook never calls the reset service.
6. **Fulfillment**: ResetPassword calls `reset.sendResetLink`: `SENT` closes `Fulfilled`;
   `NO_MFA` and `FAILED` hand off to `PasswordReset` (`NO_MFA`, `RESET_FAILED`). UnlockAccount:
   `DISABLED` accounts are never unlocked and go to `Security` (`ACCOUNT_DISABLED`); locked ones
   are unlocked and closed `Fulfilled`. ReportOutage closes `Fulfilled` with a handoff to
   `MajorIncident` when Scope resolves to `MANY`, else `GeneralSupport` (`OUTAGE_REPORTED`).
7. **FallbackIntent**: first time `ElicitIntent` with a short menu and `fallbackCount=1`;
   second time hand off (`NOT_UNDERSTOOD`) with the last utterance in the summary. Unknown intents
   hand off too.
8. **Handoff contract** (Close, read by the flow and the agent workspace): `handoff=true`,
   `handoffReason`, `handoffQueue`, `intent`, `slots` (JSON string of slot name to interpreted
   value), `summary` (one line, <= 300 chars). Successful self-service sets no handoff
   (`handoff` absent or `false`).

## Acceptance criteria (what the grader checks)

- Every response passes the structural checks in `tests/harness.ts` (`assertValidResponse`).
- Normalization, prefill from Connect, attempt counting, resolution and disambiguation behave as above.
- Confirmation never reads back the employee ID; dialog hooks never fulfill.
- Handoff attributes are complete and incoming attributes survive, on voice and chat.
- `ANSWER.md`: why this split of work between Lex configuration and the code hook, and how
  the flow consumes the contract.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests (fixtures in tests/fixtures)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w5-c1
make clean
```

Notes: the Lex input format may gain fields without a `messageVersion` change, so parse
tolerantly. `nluConfidence` is a number in the Lambda event. Lex code hook Lambda timeout is up
to 30 s, but on a voice call every second is dead air: keep backends fast.
