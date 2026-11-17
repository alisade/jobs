# Reference: javaai/ai-c1

`.grading/solution/progress_mcp/server.py`.

- Three task-shaped tools with `ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True)`.
- `learner_id` is captured by the closure in `build_server`; tools take only `course_id` / `lesson_id`.
- `enrolled()` checks the course for every call (for a lesson, the lesson's course).
- Outputs are re-shaped: progress without `quizAnswer` or `email`; lessons sorted by position;
  summaries capped at 1500 characters, HTML comments stripped, `content_trust: "untrusted"`.
- `CatalogUnavailable` becomes "unavailable ... retry"; ValueError messages tell the model what to do.

## In ADK

```python
McpToolset(connection_params=StdioServerParameters(command="python", args=["-m", "progress_mcp.server"],
           env={"KESTREL_LEARNER_ID": session_learner}),
           tool_filter=["get_learner_progress", "list_lessons", "get_lesson_summary"])
```
Remote: streamable HTTP on Cloud Run, no public ingress, ID token from the agent's service account,
learner taken from the authenticated session header the agent service sets, never from tool arguments.

## Interview angles

- "Why not mirror the REST API?" Models choose tools by name and description; fewer, task-shaped
  tools with small outputs are more accurate and cheaper in context.
- The trust label is advisory; the guarantee is that the write does not exist in this server.
