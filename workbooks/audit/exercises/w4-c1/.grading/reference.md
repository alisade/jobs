# Reference: audit/w4-c1

Reference files: `.grading/solution/durable/run.py` and `log.py`.

- **Ordering.** For each step: check the checkpoint; if absent, do the work, then commit output and the
  new state in one transaction (`put_step(..., state=...)`). A crash between work and commit repeats the
  work on restart, so the work must be idempotent (side effects) or acceptable to repeat (a model call
  that was never committed costs money once more but cannot double-publish).
- **Workpaper.** Deterministic name and deterministic bytes (built only from committed step outputs, no
  timestamps), `overwrite=False`; on `ResourceExistsError` compare and accept identical content. A
  different existing blob is an integrity problem, never an overwrite. In Azure the same effect comes
  from `If-None-Match: *` (that is what `overwrite=False` sends) or immutability policies on the container.
- **GRC.** `run_id/sample_id/step` as the Idempotency-Key on every attempt; the server deduplicates.
  Log the intent before the call so the trail shows the attempt even if the process dies mid-call.
- **Review gate.** Enforced in `review()`: state check, SoD (reviewer != preparer, case-insensitive),
  override requires reason and evidence reference. The record goes to the store (survives restarts),
  the log, and the workpaper row (`review`, `model_conclusion` vs `conclusion`) so the external auditor
  sees that a human changed the model's result and why.
- **Log.** sha256 over canonical JSON of seq/kind/data/prev. Edits break the hash, deletions and
  reorders break seq and prev. A chain alone cannot detect truncation of the newest lines: anchor
  the head hash externally (immutable blob, a GRC attachment per run).
- **Platform mapping.** Durable Functions and Temporal replay orchestrator code from history and run
  activities at-least-once, so activities need the same idempotency keys. LangGraph checkpointers
  persist graph state per step and `interrupt()` pauses for the reviewer; the side-effect rules are the same.
