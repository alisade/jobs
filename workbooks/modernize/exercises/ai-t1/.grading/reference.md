# Reference: modernize/ai-t1

Primary cause: commit 7a1c9e2 added `Current time: <seconds>` inside the system block that carries
`cache_control`. Prompt caching matches the prefix byte for byte, so every request had a new prefix: a full
cache write (about 32k tokens at the write price) on every turn and zero reads. That is the 4x on the dashboard
from 2026-11-06.

Latent causes that only show across processes: the listing is joined from a set (POD-209; string hashing is
randomized per Python process) and skills come in `glob` order (POD-207). Within one job they are stable,
which is why caching still worked in October; across jobs for the same module they defeat sharing.

Not the model: same prices, earlier commit, unchanged token counts.

Fix (`.grading/solution/migrate_agent/prompt.py`): sorted listing, skills sorted by name, the static block with
`cache_control` first, the time in a second system block after it. Guard: a unit test that builds two requests
at different times and orders and compares the prefix hash, plus an alert on cache_read share.
