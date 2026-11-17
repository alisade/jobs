# Rubric: javaai/ai-c1 A read-only learner-progress MCP server for the tutor agent
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Tool design | 15 | Task-shaped tools, names and descriptions that say when to use each and what comes back, compact outputs with renamed fields (not raw API objects), errors that tell the model what to do next. |
| 3 | Security thinking | 15 | No write path at all (not just "please do not"), learner bound to the session (confused deputy avoided), enrollment scoping, answers and PII removed, injected text stripped and labelled; ANSWER.md says labels help but enforcement is the absent write tool and server-side scoping. |
| 4 | ADK and deployment notes | 10 | McpToolset with stdio or streamable HTTP, tool_filter as a second layer, a remote server on Cloud Run with ID-token auth and the session learner from the authenticated caller, not from the model. |
| 5 | Code quality | 5 | Shared helpers for scoping and outage handling, no duplicated try/except, clear constants. |
Total: 100
