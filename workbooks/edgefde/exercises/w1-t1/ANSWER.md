# ANSWER: edgefde/w1-t1 Gaps in window counts after every consumer restart

## Approach

<!-- How you investigated: which file you opened first, which numbers you compared. -->

## Root cause

<!-- The cause, with evidence: log lines and numbers from incident/ (committed offsets vs rows in the
table at each restart), why only some pumps were hit, and why the red herrings are not it. -->

## Fix

<!-- What you changed and how you verified it (make run, make test, kill points). -->

## Trade-offs / what I would do in production

<!-- Recovering 2026-10-20 (reset offsets for the group to a timestamp, or a backfill from the archive),
real client settings, alerting that would have caught this. Short. -->
