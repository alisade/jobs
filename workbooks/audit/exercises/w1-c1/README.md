# audit/w1-c1 - Structured CM-03 evidence extraction with Gemini, Pydantic and a validation retry

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Wed: structured outputs; Thu: function calling; Fri: validation and retry)

## Scenario

Meridian Freight Holdings (MFH, fictional) is SOX-listed. Its internal audit team is building
ControlPilot, an agentic application that tests IT general controls. The first control is
**CM-03 Program change**: *every production change is approved by an authorized approver who is not
the author, the approval happens before deployment, the deployment is the ticketed change, and
automated tests passed.*

For each sampled change, ControlPilot asks Gemini to read the change ticket and pull request and to
extract the facts an auditor would test, each with a verbatim citation. Code, not the model, then
decides whether each attribute passes. The prototype "works on the demo", but the audit manager has
three objections: the Pydantic model accepts almost anything (a missing field silently becomes a
passing value), a truncated or malformed response crashes the run, and nobody can tell what the
model was asked or what it cost. You are making it audit-grade.

The model is replaced by `controlpilot/fake_gemini.py`, which returns real
`google.genai.types.GenerateContentResponse` objects from recorded scripts in `fixtures/scripts/`.
No API key, no network.

## What you have

| Path | What it is |
|---|---|
| `controlpilot/contract.py` | Pydantic contracts; `ChangeEvidence` is the draft you tighten |
| `controlpilot/extract.py` | the extraction loop you write (google-genai request, tool loop, validation retry) |
| `controlpilot/attributes.py` | deterministic attribute rules you write |
| `controlpilot/systems.py` | read-only lookups over the exported systems (complete) |
| `controlpilot/fake_gemini.py` | the fake client and response builders (complete) |
| `fixtures/` | four sampled changes, approvals, CI checks, deploy log, identity directory, recorded scripts |

## Your task

1. **Contract** (`contract.py`). Make `ChangeEvidence` and `Citation` strict: unknown keys are
   rejected; every field is required (no defaults: a field may be `null`, but the key must be
   present); `change_id` matches `CHG-` plus six digits; `pr_number > 0`; `approval_at` is
   timezone-aware or null; `tests_passed` is `true`, `false` or null; at least one citation;
   `Citation.source` is one of `ticket`, `pr`, `deploy_log`; `locator` and `quote` non-empty.
2. **Extraction loop** (`extract.py`).
   - `build_config()` returns a `types.GenerateContentConfig` with a system instruction that says
     the records are data, not instructions, and that the model reports facts with citations (not
     conclusions); `temperature=0`; JSON output with `response_schema=ChangeEvidence`; both tool
     declarations (finish `get_pr_checks(pr_number: integer)`); automatic function calling
     disabled (you run the tools yourself, so you control and log them).
   - `extract()` sends the sample (change_id, pr_number, title, author, ticket, pr) as JSON in the
     **user** content, never in the system instruction. Use `MODEL` unless told otherwise.
   - Tool loop: when the response has function calls, append the model's content, run each
     allowed tool and append a user content with one `Part.from_function_response` per call.
     A tool outside `ALLOWED_TOOLS` is never executed: answer it with an `{"error": ...}` response.
     A tool that raises returns `{"error": "<type>: <message>"}` to the model. Stop after
     `max_tool_turns` tool turns with `needs_review`.
   - Validation: a text answer must validate as `ChangeEvidence` and match the sample's
     `change_id` and `pr_number`. On failure (invalid JSON, schema error, mismatch, empty, or
     `finish_reason == MAX_TOKENS`), append a user message listing the errors and ask again, up to
     `max_attempts` answers in total; then return `status="needs_review"` with the errors. Any other
     non-STOP finish reason (SAFETY, RECITATION, ...) goes straight to `needs_review`, no retry.
   - Never raise for model or tool misbehaviour. Record `tool_calls` (every requested name, in
     order), `attempts` (text answers), and `usage` summed over every call from `usage_metadata`.
3. **Attributes** (`attributes.py`). `evaluate()` returns, in order:
   - `approval_before_deploy`: exception when there is no approver or timestamp, or when the
     approval instant is not strictly before `deployed_at` (compare instants, offsets differ);
   - `independent_approver`: exception when no approver or when author and approver resolve to the
     same employee id through the directory (logins and e-mails are aliases, case-insensitive);
     `not_evaluable` when either identity is unknown;
   - `linked_change`: the deploy record's change_id and pr_number match the evidence;
   - `tests_passed`: true pass, false exception, null not_evaluable.
   `overall()`: exception if any exception, else needs_review if any not_evaluable, else pass.
4. **ANSWER.md**: why the model extracts facts and code concludes; what you would log per call
   for an auditor; what you would change before running this on 25 samples a quarter.

## Acceptance criteria (what the grader checks)

- The contract rejects extra keys, missing keys, naive timestamps, bad ids, empty citations.
- The request: model, temperature 0, JSON + schema, AFC off, both tools declared, sample in contents.
- Tool loop: allowed tools run, disallowed tools never run, tool errors go back to the model,
  budget bounded; function responses follow function calls.
- Retry with the validation errors fed back; truncated output retried; SAFETY not retried;
  exhausted retries return `needs_review` without raising; usage summed correctly.
- Attribute rules exactly as above, including the same-instant and cross-time-zone cases.

## How to run

```bash
make setup     # builds audit/.venv once (pydantic, google-genai, google-adk, mcp, pytest)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w1-c1
make clean
```

Gemini 3 and later models accept tools together with a response schema (a preview feature at the
time of writing); on older models you would make the tool calls first and a second, tool-free call
for the structured answer. Either way the validation layer is yours.
