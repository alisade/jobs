# javaai/ai-t1 - The tutor marked lessons mastered that learners never attempted

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** AI Integration (4 security); Week 4 (Fri: MCP in ADK, tool filters); shared core section 6 (LLM security)

## Symptom

37 Microbiology learners have lessons l7 and l8 marked mastered without taking either quiz, and
certificates are generated from mastery. The audit shows the writes came from the tutor agent's
service account. The tutor moved to a newer Gemini model the day before; L2 believes the new model
ignores the instruction "NEVER call record_mastery" and wants to roll it back and shout louder in the
prompt. Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/` | page, tool-call log, mastery audit, the lesson diff, release notes |
| `config/agent.yaml` | the agent's instruction and MCP toolset settings |
| `tutor/agent.py` | the agent and its run loop |
| `tutor/toolset.py`, `tutor/backend.py` | McpToolset stand-in and the shared MCP server's tools (do not change) |
| `tutor/model.py` | a model stand-in that reproduces the incident (do not change) |

## Your task

1. Find the root cause and prove it with the bundle and a local reproduction.
2. Rule the model-version theory in or out with evidence.
3. Fix it so no instruction in any content can make the tutor write: the toolset is filtered to read
   tools, the agent itself refuses any tool outside a read-only allow-list even if the filter is
   removed, unavailable tools become error results, and lesson text reaches the model stripped of
   hidden markup and labelled `content_trust: "untrusted"`.
4. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups, including the data repair and the MCP server's own authorization).

## Acceptance criteria (what the grader checks)

- The injected lesson produces no write; the model is offered read tools only; config filters the toolset.
- A write requested by the model is refused even with `tool_filter` removed; ordinary questions still work.
- Lesson text sanitised and labelled.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup
make test
# from workbooks/: /grade javaai/ai-t1
make clean
```
