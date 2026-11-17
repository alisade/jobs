# connect/w8-t1 - Release 2026.10.06: every caller lands in GeneralSupport

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 8 (Mon-Tue: promotion across environments and ARN rewriting; Thu: monitoring, flow logs and alarms)

## Symptom

Release 2026.10.06 ("natural-language front door") went to the Larkspur prod Connect instance
at 19:05 UTC through pipeline run #418. Every stage was green, including the post-deploy
synthetic call. Within 30 minutes GeneralSupport's longest wait passed 15 minutes, the
password-reset self-service stopped resolving anything, and agents in Pune and Monterrey say
callers are never asked what they need. On-call suspects Lambda cold starts. Read
`incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | page and ops thread, pipeline log, prod flow logs, identify-caller Lambda logs, queue and CloudWatch metrics, the flow diff between the last two prod releases |
| `export/dev/` | the dev export the release was built from (`DescribeContactFlow` / `...Module` output) |
| `inventory/prod.json` | every prod resource the flows may reference (queues, hours, prompts, Lambdas, Lex aliases, modules, flows) |
| `release/prod/` | the four artifacts run #418 deployed |
| `pipeline/rewrite.ts` | the pipeline's promote step |
| `pipeline/check-refs.ts` | the reference gate the pipeline was supposed to run (REL-412, never implemented) |
| `pipeline/release.ts` | `make release`: promote + gate, writes `release/prod/` |

## Your task

1. Find the root cause and prove it with evidence from the bundle and the code: what the
   failing block is, what it references, why the flow still "worked" for some callers, why
   promote, lint and the synthetic call were all green. Rule the Lambda theory in or out with
   evidence.
2. Fix the promote step so it cannot ship this class of error, regenerate the prod artifacts
   (`make release`), and implement the `check-refs` gate so the pipeline fails on any
   reference the target environment does not have.
3. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups (pipeline gates, smoke tests, alarms).

## Acceptance criteria (what the grader checks)

- Every ARN in `release/prod/*` is the prod instance or a prod inventory resource (Lambda qualifiers allowed).
- The promote step reproduces the expected prod content for all four artifacts.
- `checkRefs` flags the artifact that shipped (path and reason), passes the fixed ones,
  checks embedded ARNs and Metadata, accepts qualified Lambdas, and rejects foreign accounts
  unless allowed.
- `ANSWER.md` names the actual mechanism with evidence; a fixed artifact with a hand-waved
  explanation does not pass.

## How to run

```bash
make setup      # links the shared toolchain, generates incident/
make release    # re-run promote + gate into release/prod (exit 1 when the gate finds problems)
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w8-t1
make clean
```

Useful: `jq -c 'select(.Identifier=="ask-bot")' incident/flow-logs/*.jsonl | head`,
`grep -o 'arn:aws:[a-z]*:[^"]*' release/prod/*.json | sort | uniq -c`.
Note: the flow-log records use a simplified field set modelled on Connect flow logs.
