# Reference: healthai/w4-c1

Reference implementation: `.grading/solution/pa_graph/graph.py`.

Key points:
- `auto_approvable(state)` is the only door to an unreviewed finalize, and it is a conjunction of
  positive checks. Unknown or invalid states fall through to review (fail closed).
- `finalize` is built by `make_finalize(threshold)` and re-checks `auto_approvable` when there is no
  `human_decision`; otherwise it raises `RuntimeError`. The module-level `finalize` uses the default
  threshold, so a unit test can call it directly.
- Reviewer input is validated inside `human_review`; an invalid value records `review_error` and a
  conditional edge loops back to `human_review`, which raises a fresh interrupt carrying the error. This
  avoids multiple `interrupt()` calls in one node (resume matching is by index within a node).
- Nodes that call `interrupt()` re-run from the top on resume, so they must be idempotent up to the
  interrupt (no side effects before it).
- The SQLite test proves resume after a restart: the checkpoint after `assess` already holds the
  recommendation, so the model is not called again.
- Production notes: `PostgresSaver` with `setup()` once; thread id `pa:<case_id>` (never member id: a
  member can have several open cases); checkpoints contain PHI, so the database is inside the BAA
  boundary with CMEK, short retention after closure and IAM-scoped access; the reviewer UI reads
  `get_state(...).interrupts`.
