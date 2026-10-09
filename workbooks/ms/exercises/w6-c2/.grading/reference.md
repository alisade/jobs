# Reference: ms/w6-c2 Dataverse Web API sync client

The reference implementation is `.grading/solution/woodgrove_sync/client.py`.

## Key points

1. Retry lives in one place (`request`). Every call path - first page, nextLink pages, upsert,
   $batch - goes through it, so throttling mid-pagination resumes on the same page with no gaps.
   Dataverse service protection limits are evaluated per user per web server over a 5-minute
   sliding window (6,000 requests, 20 minutes of combined execution time, 52 concurrent
   requests). The 429 response carries `Retry-After` in seconds; waiting exactly that long is
   the documented behaviour. Retrying sooner extends the throttle. A small jitter avoids
   synchronized retries from parallel workers. Bound the retries and cap any single wait so a
   misbehaving header cannot park the job for an hour.
2. Paging: `Prefer: odata.maxpagesize=N` must be re-sent on each page; the `@odata.nextLink`
   contains an opaque `$skiptoken` (a paging cookie) and must be used as-is. Rebuilding it from
   parsed parameters is the classic bug: double-encoding the cookie breaks paging.
3. Upsert: PATCH on the alternate key. `If-Match: *` turns it into update-only (404 when missing),
   `If-None-Match: *` into create-only (412 when present). `If-Match: W/"<etag>"` is optimistic
   concurrency (412 on mismatch). `Prefer: return=representation` gives 201 vs 200 so you can tell
   create from update (costs an extra retrieve; keep `$select` minimal). Do not put the key column
   in the body. Escape single quotes in string keys by doubling them.
4. $batch: one change set = one transaction (equivalent to ExecuteTransaction). Every request in a
   change set needs a `Content-ID`; on failure Dataverse returns 400 and only the failing
   response, so map it back to a row via the Content-ID. Batches allow up to 1,000 requests.
   For pure throughput on one table, `CreateMultiple` / `UpsertMultiple` are faster than $batch.
5. Change tracking: `Prefer: odata.track-changes` on the initial query returns
   `@odata.deltaLink` on the last page. Later calls GET that link verbatim and get new/updated rows
   then deleted rows (`@odata.context` ending in `$deletedEntity`, with `id` and `reason`).
   Persist the new delta link only after every page has been applied downstream: saving it early
   loses changes on a crash. `$filter`, `$orderby`, `$expand` and `$top` are not supported with
   change tracking. Tokens older than the organization `ExpireChangeTrackingInDays` value
   (7 days by default) fail; the recovery is a full resync followed by a fresh token.

## Common mistakes

- `time.sleep(2 ** attempt)` while ignoring Retry-After; or retrying 412/404.
- Using `params=` with requests on the nextLink (re-encodes the skiptoken).
- Saving the deltaLink from page 1, or saving before downstream writes succeed.
- Sending N single POSTs "in a batch" without a change set (not atomic).

## Interview angles

- How do you scale this to 5 parallel workers without tripping service protection?
  (Shared retry budget, honour Retry-After per connection, use more application users only
  where licensing and policy allow, prefer bulk messages.)
- Why is change tracking better than `modifiedon gt <last run>`? (Deletes, clock skew, same-
  millisecond updates, no full scans.)
