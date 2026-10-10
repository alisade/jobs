# connect/w4-c1 - Translate legacy IVR scripts into Connect flows

**Type:** coding | **Estimate:** 3 hours | **Study plan:** Week 4 (Avaya vectors and VDNs; Cisco ICM/CVP scripting; Five9 IVR scripts; concept maps onto Connect)

## Scenario

Larkspur Financial Group runs three legacy contact-center stacks: Avaya Aura Communication
Manager vectors for the main help desk, a Cisco UCCE/CVP routing script inherited from the
acquired Ridgeway Capital desk, and a Five9 VCC inbound IVR used by the Monterrey overflow
team. The migration factory (an offshore team in Pune) will hand-port about 140 legacy scripts.
To keep that honest, you are building the translator that turns an export into a first-cut
Connect flow, and the regression proof that the translated flow treats every call the way the
legacy script did. Clients reject Connect architects who cannot read a vector or an ICM script;
this exercise makes you read all three.

## What you have

| Path | What it is |
|---|---|
| `legacy/avaya/vector-14-hd-main.txt` | `display vector 14` output (VDN 47100 points at it) |
| `legacy/cisco/LFG_HD_Main.icm.xml` | ICM Script Editor routing script (simplified XML export) with CVP microapps |
| `legacy/five9/LFG_HD_Inbound.five9.xml` | Five9 IVR script (simplified XML export) |
| `config/mapping.json` | discovery-workbook mapping: legacy skill / skill group / precision queue / Five9 skill -> Connect queue, holiday table and time windows -> Connect hours of operation, VDN numbers and labels -> Connect flows, announcement and prompt ids -> prompt text, Avaya priorities -> Connect queue priority |
| `src/legacy/*.ts` | provided parsers and reference interpreters for the three formats (read their header comments: they define the semantics you must preserve) |
| `src/harness.ts` | runs a Connect flow for a call path with connect-kit and normalises the outcome |
| `src/flowBuilder.ts` | optional helper for emitting flow-language actions |
| `src/translate/{avaya,cisco,five9}.ts` | YOUR WORK: `translateAvaya`, `translateCisco`, `translateFive9` |

## Your task

1. Implement the three translators: legacy export text -> Connect flow (flow language
   `2019-10-30`) using the mapping. Concept map you need (see the study guide's Week 4 table):
   - Avaya `goto step N if holiday in table T` and `time-of-day is all A to all B`, ICM `Time`,
     Five9 `IfElse schedule:X is open` -> `CheckHoursOfOperation` on the mapped hours resource
     (holidays become hours overrides on `HelpDeskHolidays`; "inside the closed window" is the
     False branch).
   - `announcement`, CVP `PM` microapp, Five9 `Play` -> `MessageParticipant` with the mapped text.
   - `collect ... digits` + `goto ... if digits = D`, CVP `M`/`GD` + `If caller_input == V`,
     Five9 `Menu` (with `maxAttempts`) and `GetDigits` -> `GetParticipantInput` (+ `Loop` for
     retries, contact attributes and `Compare` where a value is tested later).
   - `queue-to skill S pri P`, `check skill S pri P if available-agents > 0`, ICM
     `QueueToSkillGroup` / `PrecisionQueue`, Five9 `SkillTransfer` -> set working queue, check
     staffing (staffed for queue-to, available for check), set queue priority, transfer; a failed
     queue attempt continues where the legacy script continues.
   - `route-to number`, ICM `Label` -> `TransferToFlow` to the mapped flow.
   - `disconnect after announcement`, `busy`, `stop`, ICM `End`, Five9 `Hangup` -> prompt (if any)
     then `DisconnectParticipant`.
2. Anything the mapping or Connect cannot express (e.g. an agent threshold other than `> 0`,
   which Connect's check staffing does not support) must fail loudly with an error, not be
   silently dropped.
3. Every translated flow must pass connect-kit's lint (error branches, no dead ends, bounded
   loops, attributes set before use, working queue before transfer) and start with flow logging.
4. `ANSWER.md`: your mapping decisions, what does NOT translate 1:1 (in-queue treatment after a
   queue step, VDN variables, EAS skill levels vs proficiencies, ICM percent allocation, Five9
   call variables), and how you would run the migration factory with this tool.

## Acceptance criteria (what the grader checks)

- Each translated flow is lint clean and starts with `UpdateFlowLoggingBehavior`.
- For every shipped script and three unseen scripts in the same formats, the legacy interpreter
  and the translated flow agree on every call path in a matrix of 7 call times x holiday/no
  holiday x 7 staffing variants x several key-press sequences: same outcome (queued to the same
  Connect queue at the same priority, routed to the same flow, or disconnected) and the same
  prompts in the same order.
- An unsupported construct throws.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests (lint + a few paths per format); failures print the mismatching paths
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w4-c1
make clean
```

Tip: `mismatches()` in `tests/matrix.ts` prints legacy vs Connect for each failing path; call it
from a scratch test with the full `TIMES` list while you work.

The export formats are simplified (real exports are binary .ICMS files, CM SAT screens and
Five9 Studio XML), but the step semantics follow the vendor documentation summarised in the
study guide.
