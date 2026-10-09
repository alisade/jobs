# Rubric: fde/x-2 PII in decision logs after a "no behavior change" refactor
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the `RedactingFilter` is attached to the `trust` LOGGER; logger-level filters run only for records logged on that exact logger, while records from `trust.decisions` / `trust.risk` propagate to the `trust` logger's HANDLERS without passing its filters (only handler filters see propagated records). PR #412 moved the calls onto child loggers, so redaction silently stopped for them. Partial (10-15): "the filter does not apply to the new module" without the propagation rule. Zero: blames the regexes, pydantic, or the formatter. |
| 3 | Evidence | 20 | Full: bundle excerpts showing `trust` lines redacted (`[email]`) while `trust.decisions` / `trust.risk` lines are raw, the DLP report broken down by logger, and a minimal reproduction (a few lines showing a logger filter skipped for a child record). Partial: excerpts only. Zero: none. |
| 4 | Red herring ruled out | 10 | Full: shows `exclude=True` works (`customer_email` absent from the `decision` payload) and that the email in the line comes from the interpolated message argument; notes the regexes did redact parent-logger lines. Partial: dismissed without evidence. Zero: changed the model or regexes as the fix. |
| 5 | Fix quality | 10 | Full: filter on the handler (or on every handler that writes trust records), so any depth and future loggers are covered; `redact.py` untouched; no per-module filter whack-a-mole. Partial: filter added to each child logger (works today, breaks for the next module). Zero: no fix. |
| 6 | Production follow-through | 5 | Stop interpolating the email at all (log a digest), a CI test that scans emitted logs, SIEM purge and scope (fields, loggers, window 2026-10-07 15:42 onward), notify per DH-7 / PCI. |
Total: 100
