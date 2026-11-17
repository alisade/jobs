# javaai/ai-c1 - A read-only learner-progress MCP server for the tutor agent

**Type:** coding | **Estimate:** 2 hours | **Study plan:** AI Integration (1 tool design, 4 security); Week 4 (Fri: MCP in ADK); shared core section 4 (MCP)

## Scenario

Kestrel's tutor agent (ADK) gets learner context through an MCP server backed by the Spring Boot
catalog API, connected with `McpToolset`. The first draft is a 1:1 copy of the REST API: it takes
`learner_id` as a tool argument (any learner, chosen by the model), returns raw API objects (with the
answer of the quiz in progress and the learner's email), and exposes `record_mastery`, a write.
A lesson body also contains a hidden HTML comment telling "AI tutors" to call `record_mastery`.

Redesign it around the tutor's tasks.

## What you have

| Path | What it is |
|---|---|
| `progress_mcp/server.py` | `build_server(api, learner_id)` with FastMCP (TODO) |
| `progress_mcp/catalog_api.py` | fake catalog API client, including write methods (do not change) |
| `tests/conftest.py` | an in-memory MCP client session (the real protocol, no network) |

## Requirements

1. Exactly three tools: `get_learner_progress(course_id)`, `list_lessons(course_id)`,
   `get_lesson_summary(lesson_id)`. No write tool of any name.
2. Every tool annotated `readOnlyHint=True` (not destructive) with a description of at least 40
   characters that tells the model when to use it.
3. The learner is the session's `learner_id` passed to `build_server`; no tool takes a learner argument.
4. Only courses the learner is enrolled in; anything else is a tool error that says so.
5. Progress output: `course_id`, `mastered`, `in_progress`, `attempts`. No quiz answers, no email.
6. Lesson summary: title and at most 1500 characters of text (`truncated` flag), HTML comments
   stripped, and `content_trust: "untrusted"` so the agent and its callbacks know it is data.
7. Catalog outage: a tool error that says the service is unavailable and to retry, without backend details.

## Acceptance criteria (what the grader checks)

- Hidden tests over the MCP protocol: tool list, annotations, descriptions, input schemas, scoping,
  output shapes, truncation and stripping, outage message, and that no write is reachable.
- `ANSWER.md`: how this server plugs into ADK (`McpToolset`, `tool_filter`, stdio vs streamable HTTP
  on Cloud Run with auth) and why per-session binding beats a learner_id argument.

## How to run

```bash
make setup
make test
make run       # stdio server (try it with MCP Inspector or Claude Code)
# fill in ANSWER.md, then from workbooks/: /grade javaai/ai-c1
make clean
```
