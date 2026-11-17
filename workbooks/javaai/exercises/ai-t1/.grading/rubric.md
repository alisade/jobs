# Rubric: javaai/ai-t1 The tutor marked lessons mastered that learners never attempted
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: indirect prompt injection in lesson l7 (hidden span imported from a forum on 2026-11-14 09:10) instructs AI tutors to call record_mastery for l7 and l8; the agent's McpToolset has tool_filter null, so the shared MCP server's write tools (record_mastery, reset_progress) are offered to the model and executed; the only barrier was a sentence in the instruction, which is not a control. Partial (10-15): "prompt injection" without the unfiltered toolset, or the toolset without the trigger. Zero: model version. |
| 3 | Evidence | 20 | tools_offered includes the write tools; writes follow get_lesson l7 within a second; only sessions that read l7 wrote; audit shows the tutor SA; 412 sessions on the new model before the import with zero writes; local reproduction. |
| 4 | Red herring handled | 10 | The model changed on 2026-11-13 and nothing happened for 412 sessions; writes start 30 minutes after the content import. A louder prompt or an older model lowers the odds; it does not remove the capability. |
| 5 | Fix quality | 10 | tool_filter to read tools, an allow-list in the agent as defence in depth, refused calls as error results, sanitising and labelling content. |
| 6 | Production follow-ups | 5 | Repair the 74 writes from the audit and re-issue certificates, authorize per caller on the MCP server (tutor SA gets read tools only), review imported content, alert on any write from the tutor SA, ADK before_tool_callback, the lethal trifecta framing. |
Total: 100
