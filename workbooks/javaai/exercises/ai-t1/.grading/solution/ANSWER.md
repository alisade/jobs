# ANSWER: javaai/ai-t1 The tutor marked lessons mastered

## Approach

The audit put the writes on the tutor SA. The tool-call log shows tools_offered including
record_mastery and reset_progress, and every write a second after get_lesson l7. Only sessions that
read l7 wrote. The lesson diff shows a hidden span added at 09:10. Reproduced locally with the stand-in
model: get_lesson l7, then record_mastery l7 and l8.

## Root cause

Indirect prompt injection in imported lesson content plus an unfiltered McpToolset (tool_filter null)
that hands the tutor the shared server's write tools. The instruction "NEVER call record_mastery" was
the only barrier. Not the model: 412 sessions on 2.5 Flash before the import, zero writes; writes begin
31 minutes after the import.

## Fix

tool_filter set to list_lessons and get_lesson; a READ_ONLY_TOOLS allow-list in the agent (holds even if
the filter is removed); disallowed calls become error results; lesson text stripped of hidden markup and
labelled untrusted. No writes in any test; 8/8.

## Trade-offs / what I would do in production

Revert the 74 writes and regenerate certificates. Authorize on the MCP server per caller (tutor SA gets
read tools only). Review imported content. Alert on any write from the tutor SA. Use ADK's
before_tool_callback for the allow-list.
