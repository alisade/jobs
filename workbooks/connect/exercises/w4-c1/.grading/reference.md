# Reference: connect/w4-c1

Reference translators: `.grading/solution/src/translate/` (`common.ts` holds the shared emitters).

Design:

- `Emitter` (common.ts) emits each Connect construct with every required error branch wired, so
  every translated flow is lint clean by construction: `message`, `hours`, `collect` (store input
  into a contact attribute), `compareEquals`, `queue` (set working queue -> check staffing or
  available agents -> `UpdateContactRoutingBehavior` priority -> transfer, all failures to the
  legacy fall-through), `agentsCheck`, `transferToFlow`, `start` (logging + attribute init).
- Forward references: reserve an Identifier per legacy step/node first; resolve "alias" steps that
  emit nothing (`goto ... unconditionally`, `wait-time`, `Start`, `End`/`Hangup`/`busy`/`stop` ->
  the shared disconnect) to the action they lead to, with a cycle guard.
- Polarity: hours resources are "open" when the legacy condition "inside the closed window" or
  "holiday in table" is false, so the vector's goto target is the `False` branch (the `True`
  branch for `holiday not in table`).
- Variables tested later (`digits`, `caller_input`) are initialised at the start and set from
  `$.StoredCustomerInput`, so the attribute is set on every path before any `Compare`.
- Unsupported constructs throw: a Connect check staffing condition only supports
  `NumberGreaterThan 0` for agent counts, so `available-agents in skill S > 2` cannot map.

What an interviewer wants to hear (Week 4 concept map):

| Legacy | Connect |
|---|---|
| VDN (Avaya), dialed number + call type (ICM), Five9 DNIS -> campaign | claimed number -> inbound flow |
| vector step / ICM node / Five9 module | flow block (action) |
| skill (hunt group with EAS), skill group, precision queue, Five9 skill | queue (+ routing profile; proficiencies and routing criteria for attribute-based routing) |
| pri l/m/h/t, ICM queue priority | queue priority (`UpdateContactRoutingBehavior`) and routing profile priority/delay |
| holiday table, time-of-day, ICM Time/Day of Week, Five9 schedule | hours of operation (+ overrides) |
| announcement / CVP PM microapp / Play | Play prompt (`MessageParticipant`) |
| collect digits / CVP M or GD / Menu, Get Digits | Get customer input (`GetParticipantInput`) |
| wait-time hearing music, in-queue vector loop | customer queue flow |
| route-to number / Label / External Transfer | transfer to flow, transfer to phone number, quick connect |
| adjunct routing, ICM Run External Script with DB lookup, Five9 Query module | Lambda (`InvokeLambdaFunction`) |
| VDN variables, ECC variables, call variables | contact attributes |

Production: the translator is a first cut for the migration factory, not a replacement for
review. Each ported script gets a golden call-path suite (like this matrix), flows are linted in
CI, prompts are re-recorded or moved to TTS, and cutover runs both systems in parallel with
number-by-number moves.
