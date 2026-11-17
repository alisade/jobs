# connect/w8-c1 - Flow promotion tool: dev export to test, prod and DR

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 8 (Mon: CI/CD for Connect across environments; Tue: ARN/ID rewriting and IaC coverage)

## Scenario

Larkspur Financial Group runs four Amazon Connect instances: dev (`111122223333`), test
(`222233334444`), prod and DR (`444455556666`, us-east-1 and us-west-2). Flows are built in
the dev console by the offshore team in Pune, exported with `DescribeContactFlow` /
`DescribeContactFlowModule`, and promoted by a pipeline. The pipeline's promotion script only
rewrote `QueueId` parameters, so last month's release shipped a prod flow that still invoked
the dev Lambda and the dev Lex alias (see `connect/w8-t1` for that incident). You are writing
the replacement: a promotion tool that rewrites every environment-specific reference and
refuses to emit anything that would point at the wrong account, instance or region.

There is no flow alias API for regular contact flows (versions are campaign-only; flow
modules do have versions and aliases), so the pipeline promotes the flow content itself:
`UpdateContactFlowContent` / `UpdateContactFlowModuleContent` with the artifacts you produce.

## What you have

| Path | What it is |
|---|---|
| `export/dev/flows/*.json`, `export/dev/modules/*.json` | dev export: `DescribeContactFlow` / `DescribeContactFlowModule` output; `Content` is a JSON **string** |
| `export/dev/inventory.json` | dev resource inventory: every queue, hours, prompt, Lambda, Lex alias, module and flow with its logical name, ARN and id |
| `envs/test.json`, `envs/prod.json`, `envs/dr.json` | target manifests, same shape; logical names are the join key |
| `src/types.ts`, `src/io.ts`, `src/cli.ts` | types, file IO and the CLI (provided) |
| `src/promote.ts` | the tool: a first cut that only handles `QueueId` (you finish it) |

## Requirements

Implement `promote(exp, target)` in `src/promote.ts`:

1. Rewrite every reference to a dev resource, wherever it appears in the parsed `Content`
   (any action parameter, nested objects such as `LambdaInvocationAttributes`, `LexV2Bot`,
   and the `Metadata` canvas block), whether it is the whole string value or embedded in a
   longer string (for example an ARN inside a JSON-encoded attribute).
2. Kinds: queue, hours, prompt, flow and module ARNs; bare Connect resource ids (e.g.
   `FlowModuleId`, ids passed to Lambdas); Lambda function ARNs, preserving any qualifier
   (`:live`); Lex V2 bot alias ARNs; the instance ARN and instance id.
3. Map dev -> logical name (dev inventory) -> target resource (manifest). Never guess by
   string surgery on account ids alone: the DR region and the prod instance have different
   resource ids.
4. Problems (fail closed: `ok=false` and **no artifacts** when any problem exists):
   - `unknown-reference`: a dev-owned ARN (dev account or dev instance) that is not in the
     dev inventory (a console hand-edit, a scratch Lambda);
   - `unmapped-in-target`: the dev resource exists but the target manifest has no resource
     with the same kind and logical name;
   - `dangling`: anything that still points at dev after rewriting.
   Each problem names the artifact, the JSON path and the offending value.
5. ARNs owned by other accounts (shared services) pass through untouched.
6. Artifacts: modules first, then flows; each carries `targetId`/`targetArn` of the
   same-named resource in the target (or null), the flow `type`, and `content` as a
   serialized JSON string. Output flows must still pass `connect-kit` `validateFlow`.
7. Report every replacement with `artifact`, `path` (`$.Actions[3].Parameters.QueueId`,
   `$.Metadata.ActionMetadata["set-q-vip"].queue.id`), `from`, `to`, `resource`
   (`queue:GeneralSupport`, `lambda:lfg-password-reset`, `instance`, ...).
8. Do not mutate the input.

## Acceptance criteria (what the grader checks)

- prod and DR output equals the expected target content for every flow and module.
- Qualifiers kept; Lex aliases, modules, flows, bare ids, embedded ARNs and Metadata rewritten.
- Nothing in DR output mentions us-east-1 or a dev id; nothing in prod mentions the dev account.
- Missing target resources, unknown dev ARNs and unknown dev Lambdas fail closed with precise problems.
- Foreign-account ARNs untouched; input not mutated; modules before flows; report complete.
- `ANSWER.md`: how this fits a pipeline (where it runs, what gates it, what it cannot catch).

## How to run

```bash
make setup                 # links the shared toolchain
make test                  # visible tests
make promote ENV=prod      # writes dist/prod/*.json + dist/prod/report.json (exit 1 on problems)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w8-c1
make clean
```
