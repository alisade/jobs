# connect/w5-c2 - Permission-aware RAG answers inside a voice turn

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Tue-Wed: Bedrock Converse, Knowledge Bases, Guardrails; Thu: Connect integration and latency budgets)

## Scenario

LFG wants the help desk IVR and portal chat to answer "how do I..." questions from the IT
knowledge base before queuing for an analyst. The pilot Lambda (called from the Connect flow's
AWS Lambda function block, synchronous) worked in the demo and failed the security review:

- a contractor in Pune was read a Finance-only article (no metadata filter);
- the model invented an "emergency bypass code" and cited nothing (no guardrail, no citation check);
- on a busy morning the Lambda took 11 s; Connect's synchronous limit is 8 s, so callers hit the
  flow's error branch after a long silence (SDK default retries made it worse).

Rebuild `src/rag.ts` and `src/handler.ts`. Retrieval uses `Retrieve` on the knowledge base
`KBLFGHELP01` and generation uses `Converse` with the guardrail `gr-lfg-helpdesk` v4 (contextual
grounding, prompt attack, PII filters). `RetrieveAndGenerate` is deliberately not used: it gives
you less control of the prompt, citations and latency, and it is not available on Bedrock
Managed Knowledge Bases (the direction LFG is heading, for its ServiceNow connector).

Tests replay recorded Bedrock responses (`tests/fixtures/`) with `aws-sdk-client-mock`; no AWS calls.

## Requirements

1. **Entitlements** (`entitlementsFrom`): from contact attributes the flow set after a
   server-side directory lookup: `callerVerified` ("true" only), `department`, `region`,
   `employeeType` (`employee` | `contractor`). Missing means not verified / employee.
2. **Filter** (`buildFilter`), derived only from entitlements, never from the question or model:
   - unverified: `audience` = `public-help` only;
   - employee: `audience` in `all-workers`, `all-employees`, lower-cased department;
   - contractor: `audience` in `all-workers`, `contractors`;
   - verified callers: `region` in `global` or their region; always `status` = `published`.
3. **Retrieve** with the configured KB, `numberOfResults`, `overrideSearchType`, the filter.
   Drop chunks below `minScore`. Nothing left: hand off (`NO_RELEVANT_ARTICLES`, or
   `NOT_VERIFIED_NO_ARTICLES` for unverified callers) without calling the model.
4. **Converse**: numbered sources in the user turn as `guardContent` with qualifier
   `grounding_source` and the question as `guardContent` with qualifier `query` (that is what the
   contextual grounding check evaluates); `guardrailConfig` with trace enabled; temperature 0;
   a system prompt that requires source-only answers, `[n]` citations, treats source text as data,
   and returns exactly `CANNOT_ANSWER` when the sources do not answer.
5. **Answer checks**: `guardrail_intervened` -> hand off `GUARDRAIL_INTERVENED` with the policy
   names from the trace in `handoffDetail` (never speak the canned guardrail text);
   `CANNOT_ANSWER` -> `MODEL_DECLINED`; no `[n]` -> `UNCITED`; a citation number outside the
   sources -> `BAD_CITATION`. Otherwise map citations to KB article ids (`metadata.articleId`,
   else the S3 file name), strip the markers for speech, and for chat append `(Sources: ...)`.
6. **Latency budget**: the whole answer within `budgetMs` (6500 ms in config, leaving room in
   Connect's 8 s). Retrieve gets `min(retrieveTimeoutMs, remaining)`, Converse gets what is left;
   enforce it yourself (timer + `AbortController` passed as `abortSignal`), on expiry hand off
   `TIMEOUT`. `makeClients` sets `maxAttempts` <= 2 so SDK retries cannot eat the budget.
7. **Errors** never escape: Retrieve failure `RETRIEVAL_ERROR`, Converse failure `MODEL_ERROR`,
   empty question `EMPTY_QUESTION` (no Bedrock call).
8. **Connect result** (STRING_MAP, all strings): `status` (`ANSWERED` | `HANDOFF`), `answer`,
   `citations` (comma-separated ids), `handoffReason`, `handoffDetail`, `latencyMs`.

## Acceptance criteria (what the grader checks)

- Filters per entitlement class, unaffected by question text; Retrieve parameters from config.
- Low-score chunks never reach the model; grounding qualifiers, guardrail trace, temperature 0, prompt rules.
- Every handoff reason above is produced on the matching recorded response.
- Budget: slow Retrieve or Converse is cut off near the budget, not after it; SDK maxAttempts <= 2.
- `ANSWER.md`: your latency budget arithmetic, why filters must be server-side, and the async
  alternative (Connect async Lambda mode, up to 60 s, with a holding prompt).

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w5-c2
make clean
```
