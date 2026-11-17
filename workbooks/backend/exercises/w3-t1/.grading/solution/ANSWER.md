# ANSWER: backend/w3-t1 The partner sync is missing contacts

## Approach

Compared the partner's totals with the replica counts, then followed the cursors in
`accounts-svc-access.jsonl` page by page, then reproduced with `make repro` and read `pagination.py`.

## Root cause

Keyset pagination sorts and filters on `created_at` alone, and `created_at` is not unique. The
2026-11-02 bulk load inserted 500 partner contacts in one statement, so they all share one timestamp:

```
replica-queries.txt:  2026-11-02T03:00:00.000000Z | 500
```

The cursor encodes only the last row's `created_at`, and the next page asks for `created_at > cursor`.
Page 16 ended inside the tied group (it returned 38 of the 500 tied rows, `last_created_at` is the import
timestamp); page 17 started with `cursor_after = 2026-11-02T03:00:00.000000Z` and jumped straight to
2026-11-03, skipping the other 462 tied rows:

```
accounts-svc-access.jsonl:16  "cursor_after": "2026-10-31T23:20:32.714221Z", "rows": 100, "last_created_at": "2026-11-02T03:00:00.000000Z"
accounts-svc-access.jsonl:17  "cursor_after": "2026-11-02T03:00:00.000000Z", "rows": 100, "last_created_at": "2026-11-03T23:18:16.964402Z"
partner-sync.log:              reconcile: source reports total=2431 received=1969 missing=462
make repro (starter):          pages=20 received=1969 unique=1969 expected=2431 missing=462 duplicates=0
```

The ORDER BY also leaves tie order to the engine, so even a `>=` fix would return duplicates and still
be nondeterministic. The 429s are a red herring: three requests got 429 with Retry-After, each was
retried, and the retried requests carry the same cursor and return full pages; nothing is lost there.
Before November every row had a distinct microsecond timestamp, which is why the bug was latent.

## Fix

- Sort by `(created_at, id)`, a unique and stable key; filter with the row-value comparison
  `created_at > c OR (created_at = c AND id > i)`.
- Cursor = base64url JSON `{"c": created_at, "i": id}` without padding: opaque to clients, decoded
  with validation; anything malformed raises a 400 `invalid-cursor` problem (RFC 9457).
- `limit` default 50, capped at 200, `< 1` is a 400 problem.
- Index changed to `(tenant_id, created_at, id)` so the sort and the seek are one index range scan.
- Verified: `make repro` now prints `received=2431 unique=2431 missing=0 duplicates=0`, and the
  visible tests pass.

## Trade-offs / what I would do in production

Version the cursor payload (`"v": 1`) or sign it with an HMAC so it can evolve and cannot be forged.
Tell the partner to run one full resync after the deploy; incremental syncs then catch up. Add a
contract test that walks a fixture with heavy ties, and alert when the partner's reconciliation count
differs from ours. For a sync that only needs changes, offer `updated_at`-based change feed or events
instead of repeated full walks.
