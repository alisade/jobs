# Reference: audit/w3-t1

Root cause: `COMPLETED_KEY = "temp:completed"`. In ADK, state keys with the `temp:` prefix belong to
the current invocation only and are discarded when it ends; they are never written to the session
service. Each night is a new invocation (and a new process), so `next_batch` sees no progress and
returns CHG-105101..105105 again. The exception CHG-105103 gets a second work item, and
CHG-105106..105110 are never tested.

Evidence: after two nights `run/queue.db` has two `tested` rows for each of the first five changes
and two work items for CHG-105103. The persisted state for session cm03-2026Q3 in `run/sessions.db`
has no `completed` key at all.

Red herrings: "Skipping missing token usage metadata" is ADK noting that the model response had no
usage metadata (the stand-in does not report it); the 429 was retried and succeeded.

Fix: a session-scoped key (`completed`), which ADK persists with the session. Not `user:` (shared by
every session of that user, so other samples would see this sample's progress) and not `app:`.
In production also make `test_change` idempotent (dedupe work items on change_id and sample), so a
retry or a resumed run cannot double up the reviewer queue.
