# Rubric: aiarch/ai-t1 Bedrock spend tripled after 3.1.0
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: per-request time, request id and user in the system text before the cachePoint make every prefix unique, so every turn writes and none reads. Zero: minimum size or TTL. |
| 3 | Evidence | 15 | Usage blocks before and after (write every turn, read 0), the daily cost table, the release note line, why size and TTL do not fit. |
| 4 | Fix quality | 10 | Static prefix, stable tool order, dynamic data after the cache point and still sent, question last. |
| 5 | Production view | 10 | Cache-hit alarm, prefix stability test, cost per conversation, where dynamic context belongs. |
Total: 100
