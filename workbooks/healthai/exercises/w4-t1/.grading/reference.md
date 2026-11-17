# Reference: healthai/w4-t1

PA-2290 replaced `config_for(case_id)` with a module-level `RUN_CONFIG` "to avoid allocations".
`submit_decision` sets `RUN_CONFIG["configurable"]["thread_id"]`, awaits the audit write (a real network
call in production), then calls `ainvoke(..., RUN_CONFIG)`. With three coroutines in flight, all three
set the thread id before any reaches `ainvoke`, so all three resume the last case set (PA-2026-0008 in the
replay). The first resume finalizes 0008 with md-007's denial; the next ones resume a finished thread
and overwrite the outcome. 0002 and 0003 stay at human_review. The thread id scheme (`pa:<case_id>`) is
fine: the theory about members is a red herring.

Fix: `config = config_for(case_id)` inside the call, plus a guard that the determination's case id is
the requested one. Repair: fork thread 0008 from the checkpoint before the first bad resume (time travel),
re-queue 0002 and 0003, tell Privacy which reviewer text attached to which member's case.
