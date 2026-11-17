# Rubric: aiarch/w2-t1 Access-review assistant leaks other sessions
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: the module-level specialist Agent shared across sessions accumulates history, so other sessions' data is in context; token growth explained by the same cause. Zero: temperature or prompt. |
| 3 | Evidence | 15 | Same agent_object_id across sessions, messages_in_context and input tokens rising, transcript data from another session, release note line, code line. |
| 4 | Fix quality | 10 | Per-session state, bounded (LRU + idle), thread-safe, continuity within a session preserved. |
| 5 | Production view | 10 | Runtime microVM per session vs process globals, session managers or AgentCore Memory, why prompts cannot fix it, a regression test. |
Total: 100
