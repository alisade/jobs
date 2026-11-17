# modernize/w1-t1 - The intake batch dies after the JDK 21 release

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 1 (Thu: Maven dependency mediation, BOMs, enforcer rules)

## Symptom

`claimdesk-intake` 4.13.0 went to production on Tuesday. It is the nightly batch that turns
first-notice-of-loss (FNOL) files into `claim.opened` events for reserving, fraud and
reinsurance. Two nights in a row it has processed one file and died. On-call blames JDK 21
(the same release moved the batch from JDK 8 to 21) and has drafted a rollback; the lead wants
the actual cause first. CI was green. Read `evidence/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the page and on-call thread, the batch log, the CI log, release notes, an old AppSec ticket |
| `pom.xml`, `src/` | the 4.13.0 source as released |
| `inbox/` | three of last night's FNOL files |

`make run` reproduces the failure locally; `make tree` prints the resolved dependency tree.

## Your task

1. Find the root cause and prove it: what is on the classpath, why, and which Maven rule put it
   there. Say why CI was green and whether JDK 21 has anything to do with it.
2. Fix `pom.xml` so the batch runs and every Jackson artifact converges, without breaking the
   security requirement in SEC-2291. Add a build guard so this class of conflict fails the build
   instead of production.
3. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- `make run` processes all three inbox files; the `claim.opened` v3 events and audit
  fingerprints are correct.
- At runtime jackson-core, jackson-databind and jackson-datatype-jsr310 are the same version,
  and jackson-core still meets the SEC-2291 floor.
- `pom.xml` has an enforcer rule that would have failed the 4.13.0 build, and the stale pin is gone.
- `ANSWER.md` names the Maven mechanism with evidence; "upgraded Jackson" without the why
  does not pass.

## How to run

```bash
make setup      # JDK 21 + Maven, downloads artifacts once
make run        # reproduce
make tree       # mvn dependency:tree -Dverbose
make test       # visible tests (the ones CI ran)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w1-t1
make clean
```
