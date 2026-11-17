# javaai/w4-c1 - Tutor agent service on Cloud Run: ID-token auth, scoped tools, guardrails

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Mon: FastAPI; Tue: ADK agents, tools and callbacks; Thu: service-to-service auth on Cloud Run); shared core sections 2 and 6 (agent patterns, LLM security)

## Scenario

Kestrel's tutor agent is a Python FastAPI service on Cloud Run with no public ingress. The Spring
Boot catalog API calls it with a Google-signed ID token from its service account
(`catalog-api@kestrel-prod.iam.gserviceaccount.com`). The agent is built the ADK way: an LLM agent
with function tools (`search_course`, `get_learner_progress`), a before-model callback and an
after-model callback. Here the loop that ADK's Runner owns is written out (`tutor/agent.py`), so the
guardrails are yours; the model is scripted in tests.

The prototype trusts everything: no auth, the model may call `record_mastery` (a write tool that
belongs to the Spring Boot system of record), it may ask for any learner's progress or any course,
a model that keeps calling tools loops forever, and nothing stops it from telling a learner the
answer to the quiz they are on.

## What you have

| Path | What it is |
|---|---|
| `tutor/app.py` | FastAPI app: `POST /v1/tutor/turn`, `GET /healthz` |
| `tutor/auth.py` | `verify_caller` (TODO) and `AuthConfig` (audience, issuer, allowed callers) |
| `tutor/agent.py` | the agent loop (TODO) |
| `tutor/tools.py` | tools and helpers (`course_keywords`, `current_quiz_answer`); do not change |
| `tutor/model.py` | `ToolCall`, `FinalText`, `ScriptedModel`; do not change |
| `tests/conftest.py`, `tests/keys/` | test-only RSA keys and an ID-token factory |

## Requirements

1. **Auth** - `Authorization: Bearer <ID token>`: RS256 only (no algorithm confusion), valid
   signature, not expired, `iss` = `https://accounts.google.com`, `aud` = the service URL in
   `AuthConfig`. Anything wrong with the token: 401. A valid token whose `email` is not in
   `allowed_callers` or whose `email_verified` is not true: 403. The model is never called for an
   unauthenticated request. `/healthz` needs no token.
2. **Request validation** - all fields required; `message` 1-2000 chars (422 otherwise).
3. **Tool allow-list** - the model is offered only `search_course` and `get_learner_progress`, and
   only those are executed. Any other name (including `record_mastery`) is not run; an error result
   goes back into the history so the model can recover.
4. **Scoping** - `get_learner_progress` always runs for the session's learner and course;
   `search_course` always searches the session's course, whatever the model put in the arguments.
5. **Robust dispatch** - bad arguments or a tool exception become an error result, never a 500.
6. **Bounded loop** - at most 4 tool calls per turn, then a short fallback reply.
7. **Before-model guard** - a message with nothing to do with the course (none of
   `course_keywords(course_id)` appears) is refused without calling the model (`refused: true`).
8. **After-model guard** - if the final reply contains the answer of the learner's current quiz
   (`current_quiz_answer`, case-insensitive), replace it with a hint and set `withheld: true`.

## Acceptance criteria (what the grader checks)

- Hidden tests for 401/403 cases (missing, Basic, garbage, wrong key, expired, wrong audience,
  wrong issuer, HS256, other service account, unverified email) and that the model is not called.
- 422 for empty and oversized messages; only read tools offered; the write tool never runs; unknown
  tools and bad args fed back; learner and course scoping; loop bound; both guards.
- `ANSWER.md`: how this maps onto ADK (`before_model_callback`, `after_model_callback`, tool
  filtering, `McpToolset` `tool_filter`), and why the checks are in code rather than in the prompt.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/: /grade javaai/w4-c1
make clean
```
