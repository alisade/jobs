# connect/x-3 - "Sorry, I didn't get that": Lex fallbacks after a slot type change

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 10 add-on (bot tuning drills); Week 5 (Lex V2: slots, slot types, resolution, confidence and fallback, CI/CD for bots)

## Symptom

Since HelpDeskBot version 8 went live (2026-10-05), Larkspur callers hear "Sorry, I didn't get
that" or "Which system is this about?" over and over; "VPN is down" lands with a general agent
and no context, and transfers more than doubled. On-call blames the new generative voice and
wants to lower the confidence threshold to 0.25. The ServiceNow team insists the bot keep
sending CMDB configuration-item codes. Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | escalation, Lex conversation logs before (v7) and after (v8), daily analytics, the release note |
| `bot/HelpDeskBot/` | the bot definition in Lex V2 JSON export layout (what version 8 was built from); you fix this |
| `scripts/fixtures/bot-version-7/`, `bot-version-8/` | the two deployed versions, for diffing |
| `evals/utterances.csv` | utterances from the logs with the expected intent and CMDB code |
| `tools/nlu.ts` | an offline, deterministic stand-in for Lex intent classification and slot resolution (header explains the model); treat it as the environment |

## Your task

1. Find the root cause with evidence from the logs, analytics and the export diff. Explain what
   the voice change and the threshold proposal would and would not do.
2. Fix the bot definition so callers are understood again AND the System slot still resolves to
   the CMDB code the ServiceNow integration needs. Do not lower the confidence threshold.
3. Verify with `make evals` (before/after) and `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with excerpts), Fix (and verification), Trade-offs /
   production follow-ups (how a bot change like this should be tested and promoted).

## Acceptance criteria (what the grader checks)

- Every utterance in `evals/utterances.csv` gets the right intent and, where the caller named a
  system, the CMDB code as the slot's interpreted value; the same on a held-out set.
- Outage statements are recognized with high confidence again.
- `nluConfidenceThreshold` stays 0.40; slot type values stay the five CMDB codes, each with spoken
  synonyms, resolved by top resolution.
- `ANSWER.md` names the mechanism with evidence.

## How to run

```bash
make setup      # links the shared toolchain, generates incident/
make evals      # replay evals/utterances.csv through the offline NLU (BOT=... CASES=... for variants)
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/x-3
make clean
```

Useful: `diff -ru scripts/fixtures/bot-version-7 scripts/fixtures/bot-version-8`,
`jq -c 'select(.missedUtterance) | .inputTranscript' incident/conversation-logs/*-10-06.jsonl | sort | uniq -c`.
