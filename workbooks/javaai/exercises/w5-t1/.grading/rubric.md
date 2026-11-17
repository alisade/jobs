# Rubric: javaai/w5-t1 The tutor cites the wrong lessons after a content release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: `ingest()` derives lesson ids from the position in the sorted file list (`enumerate(sorted(glob), start=1)`), ignoring the `lesson:` front matter; the content merge added `00-welcome.md`, which sorts first, so welcome became l1, transmission l2, vaccines l3, antibiotics l4; section ids and citations shift by one lesson and the labeled questions no longer match. Partial (10-15): "ids wrong" without the enumerate mechanism or the trigger. Zero: embedding model. |
| 3 | Evidence | 20 | Eval history (0.90 with model 005 on 2026-11-11, 0.05 only after PR #412), stored ids vs front matter for at least one lesson, the sample citations (right heading, wrong lesson id, l4 404), and a local run with and without 00-welcome.md. |
| 4 | Red herring handled | 10 | The model bump ran a day earlier with recall unchanged at 0.90; rolling back costs 4 h of re-embedding and fixes nothing. |
| 5 | Fix quality | 10 | Ids from front matter, validation of missing and duplicate ids, deterministic output; no reliance on file naming conventions. |
| 6 | Production follow-ups | 5 | Make the eval a blocking Cloud Build step, a link checker for citations, build the new index beside the old one and swap atomically, alert on recall drop. |
Total: 100
