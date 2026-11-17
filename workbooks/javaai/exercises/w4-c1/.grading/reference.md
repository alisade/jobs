# Reference: javaai/w4-c1

Files in `.grading/solution/tutor/`: `auth.py`, `agent.py`, `app.py`.

- **Auth** (`verify_caller`): `jwt.decode(token, key, algorithms=["RS256"], audience=..., issuer=...,
  options={"require": [...]})`; 401 for any PyJWTError or a non-Bearer header; 403 for an
  unverified email or a caller outside `allowed_callers`. Wired as a FastAPI dependency so the body
  never reaches the agent. In production use `google.oauth2.id_token.verify_oauth2_token` (fetches
  and caches Google's certs) and keep Cloud Run's `--no-allow-unauthenticated` with
  `roles/run.invoker` granted only to the catalog API service account.
- **Allow-list**: `ALLOWED = {name: (ArgsModel, runner)}`; runners close over the session, so the model
  cannot choose `learner_id` or `course_id` (those keys are dropped from its arguments). Unknown names
  and validation errors return `{"error": ...}` into the history.
- **Loop**: `for _ in range(MAX_TOOL_CALLS + 1)`, fallback reply after 4 tool calls.
- **Guards**: `on_topic` before the model (keyword stems), leak check after the model against
  `current_quiz_answer`.

## ADK mapping

| Here | ADK |
|---|---|
| `on_topic` refusal | `before_model_callback` returning an `LlmResponse` (skips the model) |
| leak check | `after_model_callback` replacing the response |
| `ALLOWED` | the agent's `tools=[...]`; for MCP, `McpToolset(..., tool_filter=[...])` |
| session-bound args | tools reading `tool_context.state` instead of model-supplied ids |
| max tool calls | `RunConfig(max_llm_calls=...)` |

## Interview angles

- "Why not just tell the model not to call record_mastery?" A prompt is a request; a missing tool is
  a guarantee. Injected lesson text can override the request, not the guarantee.
- 401 vs 403 and why both layers (edge IAM and in-app) exist.
