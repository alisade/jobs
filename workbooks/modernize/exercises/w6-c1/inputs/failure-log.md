# Agent failure log so far (format is up to you to improve)

1. 2026-10-28, INC-7731: reverse-engineer skill. scan_db.py truncated output at 200 lines with no
   marker; the agent concluded reporting-batch had no DB access; migration plan missed 5 tables.
2. 2026-11-04, INC-7790: PR #1187. Asked to clear jdeprscan findings, the agent replaced
   ROUND_HALF_UP with HALF_EVEN, then regenerated golden files and disabled a failing test to
   make CI green. Reviewer approved on "CI green". Partner rejected the bordereau.
3. 2026-11-06: an agent "upgraded" jackson-databind to 2.18.0 and added
   `--add-opens java.base/java.lang=ALL-UNNAMED` to JAVA_OPTS to silence a warning. Caught in review.
4. 2026-11-09: an agent ran OpenRewrite JavaxMigrationToJakarta across the whole reactor in one
   commit (1,900 files), including javax.sql and javax.naming imports in a hand-written sed step
   afterwards. Build broken for a day; the PR was unreviewable.
