# Rubric: aiarch/w5-t1 Tool spans start new traces
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh. Several tests are guards that pass on the starter. |
| 2 | Root cause | 30 | Full: executor worker threads do not inherit contextvars, so execute_tool spans become roots and inject a new traceparent; single calls run on the caller thread. Zero: propagators or sampling. |
| 3 | Evidence | 15 | parentSpanId null and distinct traceIds on parallel execute_tool spans, thread names, server spans parented to the orphan, the single-tool comparison. |
| 4 | Fix quality | 10 | Context copied per task (or attach/detach), parallelism kept, results with a timeout. |
| 5 | Production view | 10 | Wrapping executors or threading instrumentation, parent-based sampling, a trace-shape test in CI. |
Total: 100
