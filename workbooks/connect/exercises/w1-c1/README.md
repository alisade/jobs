# connect/w1-c1 - Harden the help desk inbound flow

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Tue: flow language and error handling; Wed: routing; Thu: Lambda in flows)

## Scenario

Larkspur Financial Group (LFG, 14,000 employees) is moving its IT service desk off an Avaya
Aura vector/VDN setup onto Amazon Connect. A contractor exported a first cut of the main
inbound flow (`flows/helpdesk-inbound.json`, flow language `2019-10-30`). In the pilot it
dropped callers silently: a slow directory lookup hung the IVR, a caller who pressed the
wrong key heard the menu forever, VIPs (the executive floor) waited behind everyone else,
and nobody could report an outage after 8 PM. The design review sign-off needs a flow that
passes the team's lint and the call-path regression suite before it goes to UAT.

You author the flow as Connect flow-language JSON, exactly what `aws connect
create-contact-flow --content` or `AWS::Connect::ContactFlow.Content` would take. Resource
ARNs are in `config/resources.json`. Locally, `connect-kit` (in `connect/_env`) lints the
graph and simulates call paths with a small interpreter; it models the subset of actions
listed below, with the error and condition semantics of the flow language reference.

## Requirements

1. Flow logging is enabled as the very first action.
2. Check `HelpDeskHours`. Closed: tell the caller the desk is closed and point them at the
   employee portal for self-service; offer "press 9 to report an outage" which routes to the
   24x7 `MajorIncident` queue; anything else disconnects politely.
3. Open: invoke `identifyCaller` (synchronous, time limit <= 3 s). On success copy
   `employeeId` and `vip` from the Lambda result into contact attributes and set
   `callerVerified=true`. On any error (including a timeout) set `callerVerified=false`,
   `vip=false`, `employeeId` empty, and continue: identification failure must never block
   the caller.
4. VIP callers (`vip == "true"`) skip the menu: `VIPDesk` queue at queue priority 1.
5. Menu: 1 password reset, 2 hardware/software (`GeneralSupport`), 3 outage
   (`MajorIncident`, priority 1). Up to 3 attempts in total on timeout or invalid key, with
   a short "sorry" between attempts, then route to `GeneralSupport` (never drop).
6. Password reset: invoke `passwordReset` (time limit <= 8 s) passing `employeeId` and
   `callerVerified`. `resetStatus == "SENT"`: confirm and disconnect. Anything else (other
   status or a Lambda error): `PasswordReset` queue.
7. Before transfer, check staffing (`NumberOfAgentsStaffed`) on the working queue. None
   staffed: tell the caller and overflow to `GeneralSupport`.
8. Transfer to queue handles `QueueAtCapacity` (message, then disconnect) and other errors
   (technical-difficulties message, then disconnect).
9. Never read an employee identifier back in a prompt.

Graph rules enforced by `make lint` (same rules the grader uses): every action's required
error branches are wired, no dead ends, every cycle is bounded by a `Loop` block, no
`$.Attributes.x` or `$.External.x` used before it is set on every path, every transfer has a
working queue on every path, synchronous Lambda limits within Connect's 8 seconds.

Supported action types: `UpdateFlowLoggingBehavior`, `CheckHoursOfOperation`,
`InvokeLambdaFunction`, `UpdateContactAttributes`, `Compare`, `UpdateContactTargetQueue`,
`UpdateContactRoutingBehavior` (`QueuePriority`), `Loop`, `GetParticipantInput`,
`MessageParticipant`, `CheckMetricData`, `TransferContactToQueue`, `DisconnectParticipant`
(and a few more; see `connect/_env/connect-kit/flow.js`).

## Acceptance criteria (what the grader checks)

- `make lint` reports no errors.
- Call paths: menu options, retries then fallback, VIP bypass with priority, outage priority,
  identify error and identify slower than its limit, reset success/failure/error, staffing
  overflow, queue at capacity, after-hours outage option, after-hours portal message.
- Lambda budgets: identify <= 3 s, every synchronous invoke <= 8 s, every invoke has an error branch.
- `ANSWER.md`: why each budget and fallback, and what you would change before production.

## How to run

```bash
make setup                          # links the shared toolchain (first run installs ~300 MB once)
make lint                           # graph rules
make simulate INPUTS='-,7,2'        # one call path ('-' = timeout); OPEN=false VIP=true IDENTIFY=timeout RESET=FAILED STAFFED=0
make test                           # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w1-c1
make clean
```

Real-world note: the console exports UUID identifiers and a `Metadata` block with canvas
positions; readable identifiers are fine for the flow language, and the console regenerates
layout on import.
