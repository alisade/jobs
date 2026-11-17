# healthai/w6-t1 - Member names in exported spans, with redaction switched on

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (Tue de-identification; Wed PHI flow map and audit logs)

## Scenario

Information Security found member names and member ids in about 3% of the trace spans Kestrel Health
Plan's (fictional) PA assistant sends to its tracing vendor, and in a sample of log lines. Both log
handlers have a redaction filter and the span exporter scrubs attributes. Vendor exports are paused
until you explain it. Read `incident/ticket.md`.

## What you have

| Path | What it is |
|---|---|
| `incident/ticket.md`, `incident/scan_report.txt` | the ticket and the scanner output (`make setup`) |
| `app/redact.py` | the redaction function (works as designed; do not change it) |
| `app/logsetup.py` | the JSON log handler, the log-to-span-event bridge and `RedactFilter` |
| `app/tracing.py` | a small tracer whose exporter scrubs attributes |
| `app/pipeline.py` | runs 300 synthetic cases and writes `out/app.log.jsonl` and `out/spans.json` |
| `scripts/scan.py` | Security's scanner (`make scan`) |
| `findings.json` | your machine-checked findings |

## Your task

1. Reproduce with `make setup` / `make scan`; find which records leak and what they have in common.
2. Find the root cause. Decide whether the exporter's nested-attribute TODO is involved, with evidence.
3. Fix it so that every way the code can log is covered: `%`-style args, mapping args, f-strings,
   string `extra=` fields and exception text, in the log sink and in span events. Keep messages useful
   (`"eligibility retry for [NAME] member [MEMBER]"`).
4. Fill in `findings.json` (file, class, the leaking log call, the span leak percentage before the fix,
   the red herring) and `ANSWER.md`, including what was exposed and to whom.

## Acceptance criteria (what the grader checks)

- No roster name or member id in handler output or exported spans for any logging style.
- The pipeline end to end exports nothing identifiable; span attributes stay scrubbed.
- `findings.json` matches the evidence.

## Run

```
make setup && make scan && make test
# fill in ANSWER.md and findings.json, then from workbooks/ in Claude Code: /grade healthai/w6-t1
make clean
```
