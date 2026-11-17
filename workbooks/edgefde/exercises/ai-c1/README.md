# edgefde/ai-c1 - Operator assistant on a local model: read-only tools, validated answers, hybrid routing

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** AI Integration page (tool design, the agent loop, security, evals); Week 6 (Tue-Wed: LLMs at the edge, hybrid routing)

## Scenario

Corvane's Dunmore operators (fictional) want to ask "why did machine 4 alert at 14:05?" on the
control-room PC and get an answer grounded in the pipeline data, not a guess. The plant network has
no internet by default, so the assistant runs on a small local model on the level 3 server (llama.cpp
or Ollama in production). A cloud model may be used only when the plant's policy flag allows it, and
raw waveforms never leave the site.

Here the model is a stub (`assistant/llm.py`) that replays recorded responses in the
OpenAI-compatible shape that Ollama and the llama.cpp server return, so everything runs offline and
deterministically. The hidden eval suite is a set of recorded conversations.

## What you have

| Path | What it is |
|---|---|
| `assistant/llm.py` | `StubLLM(name, script, latency_ms)`: `chat(messages, tools)` returns the next recorded turn (do not edit) |
| `assistant/data.py` | alerts, feature history, model card, one raw capture (do not edit) |
| `assistant/schema.py` | the answer contract (TODO) |
| `assistant/tools.py` | read-only tools, their schemas, dispatch (TODO; schemas given) |
| `assistant/agent.py` | the agent loop (TODO) |
| `assistant/router.py` | local vs cloud routing (TODO; `Policy` and `is_complex` given) |

## Your task

### Answer contract (`schema.py`)
`answer` 1-1200 chars, `citations` at least one string, `confidence` in [0, 1], `recommended_action`
from the `Action` enum (none of which changes device or model state).

### Tools (`tools.py`)
`get_alerts(machine, since=None)`, `get_feature_history(machine, start, end)`, `get_model_card()`,
`get_raw_capture(machine)`. Return copies (callers must not be able to mutate `data`). Unknown machine,
bad ranges and bad arguments return `{"error": "..."}` with a message the model can act on.
`schemas(include_local_only)` omits `LOCAL_ONLY` tools when False. `dispatch(name, arguments, allowed)`
never raises: unknown or not-allowed tools return an error result.

### Agent loop (`agent.py`)
`run(llm, question, max_turns=6, max_retries=1, include_local_only=True) -> AgentResult`:
- messages start with the system prompt and the question; each turn calls `llm.chat(messages, schemas)`
- tool calls (possibly several in one turn) are executed in order and each result goes back as
  `{"role": "tool", "tool_call_id": id, "content": json.dumps(result)}`, after the assistant turn
- a text turn is parsed as `Answer`; it is valid only if every citation is the id of a tool call
  executed in this conversation; on failure append a user message that contains the validation error
  and retry, at most `max_retries` times, then `status="invalid"`
- statuses: `ok`, `invalid`, `max_turns` (no answer within `max_turns` model calls), `error` (the
  client raised); `latency_ms` is the sum of `llm.latency_ms` over the calls made

### Router (`router.py`)
`answer(question, local, cloud, policy)`: if `allow_cloud` and `cloud_for_complex` and `is_complex`,
go straight to cloud; otherwise local, and fall back to cloud only if the local status is not `ok` and
`allow_cloud`. The cloud run never gets local-only tools (so no raw samples reach it). Set
`result.model` to `"local"` or `"cloud"`; on fallback `latency_ms` includes the failed local attempt.

## Acceptance criteria (what the grader checks)

- 18 recorded scenarios: citations, parallel calls, retry with the error fed back, invalid after two
  bad replies, citation and enum checks, recoverable tool errors, max turns, no mutation, routing
  decisions, no raw data to the cloud, latency accounting.
- `ANSWER.md`: why validation and citation checks are enforced in code, what you would measure on the
  real local model (accuracy per scenario, latency per answer on the target hardware), and how the
  router policy would be governed.

## How to run

```bash
make setup && make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/ai-c1
```

## What to submit

Your changes under `assistant/` and a filled-in `ANSWER.md`.
