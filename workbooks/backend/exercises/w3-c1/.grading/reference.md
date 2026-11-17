# Reference: backend/w3-c1 Idempotency keys that survive concurrent retries

Reference implementation: `.grading/solution/app/idempotency.py`; model answer in
`.grading/solution/ANSWER.md`.

The starter is check-then-insert: every concurrent retry passes the check during the handler's
directory call. The fix makes the database's primary key `(tenant_id, key)` the single arbiter:
INSERT an `in_progress` claim first; only the winner runs the handler; it then completes (stores the
response) or releases (deletes) the row. Everyone else reads the row and answers 422 (fingerprint
mismatch), 409 with Retry-After (in progress) or replays the stored response.

Points interviewers probe:
- Why an in-process lock is wrong (several pods, several workers).
- The gap between the handler's commit and the completion write; Stripe and Brandur solve it with
  recovery points or by committing the business row and the key update together.
- Fingerprinting: canonical JSON, and including the path so a key cannot be reused across endpoints.
- What not to replay: 5xx (release instead), and very large bodies (store a reference).
