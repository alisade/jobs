# Reference: backend/w3-t1 The partner sync is missing contacts

Injected fault: `contacts_api/pagination.py` sorts by `created_at` only and the cursor holds only the
last `created_at`, filtered with `>`. Any page boundary inside a group of identical timestamps skips
the rest of the group. The 2026-11-02 bulk load gave 500 rows one timestamp; with limit 100 the partner
lost 462. The fixed files are in `.grading/solution/contacts_api/` (pagination.py, db.py) and the model
answer in `.grading/solution/ANSWER.md`.

Key points: keyset pagination needs a unique, stable ordering (append the primary key as a tie
breaker), the cursor must carry every sort column, the index should match the sort, and cursors are
opaque and validated. AIP-158 and the Relay connections spec say the same thing.

## Interview angles
- "Why not offset pagination?" (Cost grows with the offset, and inserts shift pages: skips and duplicates.)
- "The partner wants only changes since last night. What do you offer?" (An `updated_at, id` keyset feed
  with a small overlap window, or events from the outbox; deletes need tombstones.)
- "Would `>=` have fixed it?" (No: duplicates, and with a group larger than the page size it loops forever.)
