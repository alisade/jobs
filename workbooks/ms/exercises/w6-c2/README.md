# ms/w6-c2: Dataverse Web API sync client (paging, 429, $batch, upsert, change tracking)

Type: coding. Estimate: 2.5-3 h. Exam: AB-400 - Extend the platform (35-40%): Web API, service
protection limits; Develop integrations (10-15%): change tracking, alternate keys, upsert.

## Scenario

Woodgrove Utilities keeps its field asset register (pumps, valves, chillers) in Dataverse table
`contoso_asset` (entity set `contoso_assets`, alternate key `contoso_assetcode`). The nightly sync
to the GIS platform is a Python job written by a contractor who has left. Last month it:

- re-imported 40,000 rows every night instead of only the changes,
- died halfway through on `429 Too Many Requests` after Dataverse service protection kicked in,
  then retried in a tight loop and got the application user throttled for 5 minutes,
- created duplicate assets because it used POST instead of an upsert on the alternate key,
- left half a work package behind when one row of a bulk create failed.

You are rewriting the client. There is no Dataverse here: `fakedataverse/` is a local fake of
the Dataverse Web API v9.2 that runs on 127.0.0.1 inside the tests and models the documented
behaviours (read the docstring at the top of `fakedataverse/server.py`; do not edit it).

## Your task

Implement the TODOs in `woodgrove_sync/client.py`:

1. `request()` - one HTTP call with service-protection retry: on 429 wait the `Retry-After`
   seconds (via `time.sleep`; the tests patch it), cap a single wait at `max_retry_after`, retry at
   most `max_retries` times, then raise `ThrottledError`. Never retry other errors.
2. `list_all()` - page with `Prefer: odata.maxpagesize=N` and follow `@odata.nextLink`.
3. `upsert_by_key()` - PATCH on the alternate key `contoso_assets(contoso_assetcode='A-1')` with
   modes `upsert`, `create_only` (`If-None-Match: *`), `update_only` (`If-Match: *`) and optional
   optimistic concurrency (`etag`). Return `"created"` or `"updated"`.
4. `batch_create()` - one `$batch` POST containing ONE change set, a `Content-ID` per request;
   return the new ids in input order; on failure raise `BatchError` with the failing row index.
5. `sync_changes()` - change tracking: initial full load with `Prefer: odata.track-changes`, later
   runs from the stored `@odata.deltaLink`; apply upserts and deletes; persist the new delta link.

## Acceptance criteria

- `nextLink` and `deltaLink` URLs are used exactly as returned (never parsed or rebuilt), and the
  `Prefer` header is sent again on every page.
- 429 handling waits `Retry-After` seconds, gives up after `max_retries` retries, and does not
  retry 4xx errors such as 404 and 412.
- Upsert never creates duplicates, escapes quotes in string key values (`'O''BRIEN'`), does not
  send the key column in the body, maps 404 and 412 to `RecordNotFoundError` and
  `PreconditionFailedError`, and rejects unknown modes with `ValueError`.
- `batch_create` is atomic (all or nothing), sends a single HTTP request, rejects more than 1,000
  rows (the documented per-batch limit) and does nothing for an empty list.
- `sync_changes` handles deleted rows (`.../$deletedEntity` items with `id` and `reason`), and
  saves the new delta link only after every page has been applied, so a crash halfway through
  does not lose changes.
- `make test` passes. The hidden tests cover the failure paths above.

## How to run

```
make setup     # uv sync
make test      # visible tests (happy paths)
```

Then from the workbooks root: `/grade ms/w6-c2`.

## What to submit

- `woodgrove_sync/client.py`
- `ANSWER.md`: approach, fix notes, and production trade-offs. Cover how you would size
  `max_retries`, what you would do when the change-tracking token has expired (the
  organization's `ExpireChangeTrackingInDays` setting, 7 days by default), and when you would
  pick `CreateMultiple`/`UpsertMultiple` or `ExecuteMultiple` over `$batch`.

## Study guide links

- [Study plan Week 6 Thu - Web API, SDKs, limits, bulk](../../../../microsoft-adf-powerapps-study-plan.html#week6)
- [Study plan Week 7 Fri - Dataverse events and data sync](../../../../microsoft-adf-powerapps-study-plan.html#week7)
- [Service protection API limits](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/api-limits)
- [Query data: page results](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/query/page-results)
- [Execute batch operations using the Web API](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api)
- [Update and delete (upsert)](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/update-delete-entities-using-web-api)
- [Perform conditional operations](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/perform-conditional-operations-using-web-api)
- [Use change tracking to synchronize data](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/use-change-tracking-synchronize-data-external-systems)
