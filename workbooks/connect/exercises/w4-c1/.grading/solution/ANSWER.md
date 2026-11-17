# ANSWER: connect/w4-c1 Translate legacy IVR scripts into Connect flows

## Approach

Read the three interpreter headers first and wrote a concept table (step -> Connect block). Built
one Emitter with every construct pre-wired for its required error branches, then three thin
front ends. Each front end reserves an Identifier per legacy step/node and resolves alias steps
(unconditional goto, wait-time, Start, End/Hangup/busy/stop) so forward gotos are easy. Used the
path matrix from tests/matrix.ts on all 7 times while iterating.

## Fix

- Hours: holiday tables -> HelpDeskHolidays hours (closed on holidays), time windows -> the mapped
  hours resource; the legacy goto target is the False (closed) branch.
- Prompts: mapped text in MessageParticipant / GetParticipantInput so the prompt sequence matches.
- Input: GetParticipantInput with StoreInput, copied into an attribute (digits / caller_input /
  Five9 variable) that is initialised at start; Five9 Menu uses Loop(maxAttempts).
- Queues: set working queue -> CheckMetricData (staffed for queue-to/skill transfer, available for
  check) -> QueuePriority from the mapping -> transfer; failure and QueueAtCapacity continue at the
  legacy fall-through.
- Routes: route-to number / Label -> TransferToFlow.
- Unsupported thresholds and missing mapping entries throw.

## Trade-offs / what I would do in production

Not 1:1: in-queue treatment after queue-to (customer queue flow), VDN variables and VDN override
(contact attributes / flow parameters), EAS skill levels (proficiencies and routing criteria, or
routing profile priority/delay), ICM percent allocation (DistributeByPercentage), Five9 Query
modules (Lambda). Factory: generate, lint in CI, golden path suite per script signed off by the
business owner, human review of every flow, parallel run per number block before porting.
