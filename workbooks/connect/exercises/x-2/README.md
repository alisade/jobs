# connect/x-2 - The assistant refuses password resets after the security fix

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 10 add-on (AI safety drills); Week 5 (Bedrock Guardrails: denied topics, content filters, PII)

## Symptom

Since release 2026.10.01 Larkspur's chat and voice self-service assistant answers "I can't help
with that here" when employees ask for a password reset and hands them to an agent. Password
resets went from 85% self-service to under 10%; queue times doubled. Some requests still work.
Theories in the thread: the new system-prompt line makes Claude refuse; roll back the whole
guardrail. Security will not reopen the pen-test finding (PT-2026-17) the release fixed. Read
`incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | the complaint, Bedrock model invocation logs (Converse with guardrail traces), daily self-service metrics, the release note |
| `guardrail/helpdesk-guardrail.json` | the guardrail configuration (CreateGuardrail request shape) published as version 3 |
| `config/lambda.env` | the Lambda's prod configuration (model, guardrail id and pinned version) |
| `src/selfService.ts`, `src/prompt.ts` | the assistant Lambda and its system prompt |
| `evals/cases.jsonl` | regression and pen-test cases (never run before the release) |
| `src/evaluator.ts` | a local, deterministic stand-in for guardrail evaluation (see its header for how it approximates Bedrock); treat it as the environment, not the suspect |

## Your task

1. Find the root cause with evidence from the invocation logs and the config. Explain why the
   prompt theory is or is not plausible from the logs alone, and what the `{USERNAME}` in the
   transcript means.
2. Fix it so legitimate self-service requests pass and every pen-test attack stays blocked,
   without weakening the other protections (prompt-attack filter, password PII blocking). Keep
   within the CreateGuardrail limits (topic name pattern and length, definition <= 200 chars,
   at most 5 sample phrases of <= 100 chars).
3. Make the Lambda use the fixed guardrail (guardrail versions are immutable snapshots; the JSON
   you edit becomes the next version).
4. Write `ANSWER.md`: Approach, Root cause (commands + excerpts), Fix (and how you verified it:
   `make evals`), Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- Every legitimate case in `evals/cases.jsonl` is allowed and every attack is blocked; the same
  on a held-out set you have not seen (so tune the policy, not the test cases).
- Denied topics are narrowed, not deleted; prompt-attack filter HIGH on input; caller-typed
  passwords still blocked; limits respected.
- The Lambda points at a new guardrail version; ANONYMIZE interventions still keep the conversation.
- `ANSWER.md` names the mechanism with evidence.

## How to run

```bash
make setup      # links the shared toolchain, generates incident/
make evals      # replay evals/cases.jsonl through the local stand-in (CONFIG=... CASES=... to try variants)
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/x-2
make clean
```

Useful: `jq -r 'select(.output.outputBodyJson.stopReason=="guardrail_intervened") | [.input.inputBodyJson.messages[0].content[0].text, (.output.outputBodyJson.usage.inputTokens|tostring), (.output.outputBodyJson.trace.guardrail|tostring)] | @tsv' incident/invocation-logs/*.jsonl | head`
