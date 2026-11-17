# modernize/w4-t1 - The mainframe rejects September's claims extract

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 4 (Thu: blast radius; Fri: parallel runs and rollback) and Week 1 (what JDK 9-21 changed)

## Symptom

The pod is running a parallel run before the JDK 21 cutover (CHG-88240): the reconciliation
extract is produced on JDK 8 (prod) and JDK 21 (staging) from the same August-October 2025
data, and both go to the mainframe test region. August and October are byte-identical and
accepted. September is rejected by CLMRECON-T, every record, RC=12. The pod suspects the
JDK 18 default-charset change or a tzdata update. Go/no-go is Monday. Read `evidence/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the change thread, the mainframe reject report, the copybook, the JDK 8 and JDK 21 extracts for all three months, the staging launcher and its system properties |
| `src/main/java/.../ExtractWriter.java` | the fixed-width writer (since 2011) |
| `src/main/java/.../ExtractJob.java` | the batch entry point |
| `data/` | the replayed paid-loss inputs |

## Your task

1. Find the root cause and prove it: what differs in the September files, byte by byte, and which
   JDK change produced it. Rule the charset and tzdata theories in or out with evidence.
2. Fix the writer so the file contract no longer depends on the JDK's locale data, and so a
   field that would not fit fails the job instead of shipping a shifted record.
3. Blast radius: list which other outputs of a monolith like ClaimDesk carry the same exposure,
   and how you would find them (search patterns, a characterization test per output).
4. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups (go/no-go recommendation included).

## Acceptance criteria (what the grader checks)

- All twelve months use the copybook's abbreviations; records are 45 bytes; output does not depend
  on the default locale.
- The JDK 21 output for August, September and October is byte-identical to the JDK 8 production files.
- Over-wide fields throw; the job writes ASCII.
- `ANSWER.md` names the JDK change with evidence and covers the blast radius; a workaround
  flag without explanation does not pass.

## How to run

```bash
make setup                 # JDK 21 + Maven, downloads artifacts once
make run MONTH=2025-09     # reproduce on JDK 21
make test                  # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w4-t1
make clean
```

Useful: `diff evidence/CLMRECON.2025-09.jdk8-prod.dat evidence/CLMRECON.2025-09.jdk21-staging.dat | head`,
`awk '{ print length($0) }' <file> | sort | uniq -c`.
