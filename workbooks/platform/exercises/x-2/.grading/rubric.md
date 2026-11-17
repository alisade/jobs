# Rubric: platform/x-2 Chart 3.0 reached every cluster at once
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the stable ApplicationSet's `targetRevision: '>=2.0.0'` (commit 5aa81c3) is an unbounded semver range that resolved to 3.0.0 as soon as 3.0.0 was published at 15:02; periodic refresh at 15:06 made prod OutOfSync and automated sync applied it; prod values still had db.url. Notes that 3.0.0-rc.1 did not match because pre-releases are excluded. Partial (10-15): "stable picked up 3.0.0" without the range semantics or the publish timing. Zero: blames selfHeal or the canary commit. |
| 3 | Evidence | 20 | Full: at least three quoted pieces: the live source `targetRevision: '>=2.0.0'`, the events `resolved targetRevision '>=2.0.0' to 3.0.0`, app history revision 42 at 15:06, index `created` 15:02:41, git show of 5aa81c3, simulator output. Partial: one or two. Zero: assertion only. |
| 4 | Red herring handled | 10 | Explains that selfHeal reverts live drift and does not pick versions; automated sync widened the blast radius but is not the defect. |
| 5 | Fix quality | 5 | Stable pinned or bounded within the major; canary unchanged; selectors still cover every cluster once; names and value files untouched. |
| 6 | Production follow-ups | 10 | Concrete: CI check on targetRevision ranges, promotion by PR or progressive sync by wave with health gates, breaking chart releases fail fast on old keys, prod values shipped with the bump, alert on prod revision changes, audit other ApplicationSets. |
Total: 100
