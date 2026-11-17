# Reference: aiarch/w2-c1

See `.grading/solution/helpdesk/`. Key points: specialists are created inside the tool call
(fresh state per request, see w2-t1 for what goes wrong otherwise); AuditHook sets
`event.cancel_tool` for delete_* in BeforeToolCallEvent and records the result status in
AfterToolCallEvent; BudgetHook raises in BeforeModelCallEvent. A specialist's exception becomes
an error tool result for the orchestrator (Strands catches tool exceptions), while an
exception in the orchestrator's own loop surfaces to the caller wrapped in EventLoopException.
