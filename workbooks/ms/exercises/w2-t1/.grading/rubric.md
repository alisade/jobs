# Rubric: ms/w2-t1 Live fleet dashboard flat since 09:40
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 35 | Full: producer 4.2.0 envelope change (device.id, tsMs epoch ms, telemetry.*) vs the unchanged ingestion mapping; missing paths land as nulls (no ingestion failure); the update policy filter then drops every row. Partial (15): "schema change" without the mechanism, or blames the update policy. Zero: capacity throttling or Eventstream. |
| 3 | Evidence | 15 | Full: cites eventstream metrics (flowing, 0 errors), landing vs enriched counts, null profile, the deployed mapping, the git diff, and rules out capacity with timestamps. Partial: two or three of these. |
| 4 | Fix quality and verification | 10 | Full: correct paths and DateTimeFromUnixMilliseconds, applied via .alter ingestion mapping, verified with replay and a post-fix query; data-quality filter and transactional policy kept. Partial: works but unverified. |
| 5 | Backfill and prevention | 10 | Full: concrete backfill of the 09:40-fix window (raw lakehouse copy or Eventstream retention, delete null rows) plus null-ratio/freshness alerting and a producer contract or raw dynamic column. Partial: one of these. |
Total: 100
