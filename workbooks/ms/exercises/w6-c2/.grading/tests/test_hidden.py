"""Hidden tests for ms/w6-c2."""
import pytest

from woodgrove_sync.client import (BatchError, DataverseClient, PreconditionFailedError,
                                   RecordNotFoundError, ThrottledError, TokenStore)

SET = "contoso_assets"
COLS = ["contoso_assetcode", "contoso_name", "contoso_site"]


def _gets(server):
    return [r for r in server.fake.requests if r["method"] == "GET"]


# ---- throttling ------------------------------------------------------------
def test_retry_after_is_honoured(server, sleeps):
    server.fake.seed(2)
    server.fake.throttle(2, retry_after=7)
    rows = DataverseClient(server.api_url).list_all(SET, COLS)
    assert len(rows) == 2
    assert len(sleeps) == 2, "one sleep per 429"
    assert all(7 <= s < 9 for s in sleeps), f"must wait Retry-After seconds (7), slept {sleeps}"


def test_retry_cap_raises_throttled_error(server, sleeps):
    server.fake.throttle(50, retry_after=1)
    client = DataverseClient(server.api_url, max_retries=3)
    with pytest.raises(ThrottledError):
        client.list_all(SET, COLS)
    assert len(server.fake.requests) == 4, "1 attempt + 3 retries, then give up"
    assert len(sleeps) == 3


def test_retry_after_is_capped(server, sleeps):
    server.fake.throttle(1, retry_after=3600)
    client = DataverseClient(server.api_url, max_retry_after=30)
    client.list_all(SET, COLS)
    assert sleeps and sleeps[0] <= 31


def test_non_429_errors_are_not_retried(server, sleeps):
    client = DataverseClient(server.api_url)
    with pytest.raises(RecordNotFoundError):
        client.upsert_by_key(SET, {"contoso_assetcode": "NOPE"}, {"contoso_name": "x"}, mode="update_only")
    assert sleeps == []
    assert len(server.fake.requests) == 1


def test_throttle_mid_paging_resumes_same_page(server, sleeps):
    server.fake.seed(6)
    client = DataverseClient(server.api_url)
    # let page 1 succeed, then throttle the nextLink request once
    orig = client.session.request
    calls = {"n": 0}

    def wrapped(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 2:
            server.fake.throttle(1, retry_after=2)
        return orig(*a, **kw)

    client.session.request = wrapped
    rows = client.list_all(SET, COLS, page_size=4)
    assert len(rows) == 6
    assert len({r["contoso_assetid"] for r in rows}) == 6, "no duplicates or gaps after a 429"


# ---- paging ----------------------------------------------------------------
def test_next_link_used_verbatim_and_prefer_resent(server):
    server.fake.seed(5)
    client = DataverseClient(server.api_url)
    rows = client.list_all(SET, COLS, page_size=2)
    assert len(rows) == 5
    gets = _gets(server)
    assert len(gets) == 3, "page size 2 over 5 rows is 3 requests (Prefer must be re-sent on every page)"
    for g in gets:
        assert "odata.maxpagesize=2" in g["headers"].get("prefer", "")
    # every follow-up target must be exactly the nextLink the server returned
    for g in gets[1:]:
        assert "$skiptoken=%3Ccookie" in g["target"], f"nextLink was rebuilt or re-encoded: {g['target'][:120]}"


def test_select_is_sent(server):
    server.fake.seed(1)
    DataverseClient(server.api_url).list_all(SET, ["contoso_name"])
    assert "$select=contoso_name" in _gets(server)[0]["target"]


# ---- upsert ----------------------------------------------------------------
def test_create_only_on_existing_raises_412(server):
    client = DataverseClient(server.api_url)
    client.upsert_by_key(SET, {"contoso_assetcode": "K-1"}, {"contoso_name": "a"})
    with pytest.raises(PreconditionFailedError):
        client.upsert_by_key(SET, {"contoso_assetcode": "K-1"}, {"contoso_name": "b"}, mode="create_only")
    assert server.fake.by_code("K-1")["contoso_name"] == "a"
    assert server.fake.requests[-1]["headers"].get("if-none-match") == "*"


def test_update_only_on_missing_raises_404_and_creates_nothing(server):
    client = DataverseClient(server.api_url)
    with pytest.raises(RecordNotFoundError):
        client.upsert_by_key(SET, {"contoso_assetcode": "GONE"}, {"contoso_name": "x"}, mode="update_only")
    assert server.fake.count() == 0
    assert server.fake.requests[-1]["headers"].get("if-match") == "*"


def test_etag_mismatch_raises_412(server):
    client = DataverseClient(server.api_url)
    client.upsert_by_key(SET, {"contoso_assetcode": "E-1"}, {"contoso_name": "a"})
    current = server.fake.by_code("E-1")["versionnumber"]
    with pytest.raises(PreconditionFailedError):
        client.upsert_by_key(SET, {"contoso_assetcode": "E-1"}, {"contoso_name": "b"}, etag='W/"1"')
    assert client.upsert_by_key(SET, {"contoso_assetcode": "E-1"}, {"contoso_name": "c"},
                                etag=f'W/"{current}"') == "updated"


def test_key_with_quote_is_escaped(server):
    client = DataverseClient(server.api_url)
    assert client.upsert_by_key(SET, {"contoso_assetcode": "O'BRIEN-7"}, {"contoso_name": "x"}) == "created"
    assert server.fake.by_code("O'BRIEN-7") is not None


def test_key_not_sent_in_body(server):
    client = DataverseClient(server.api_url)
    client.upsert_by_key(SET, {"contoso_assetcode": "N-1"}, {"contoso_name": "x", "contoso_assetcode": "N-1"})
    client.upsert_by_key(SET, {"contoso_assetcode": "N-1"}, {"contoso_name": "y"})
    assert server.fake.count() == 1


def test_unknown_mode_rejected(server):
    with pytest.raises(ValueError):
        DataverseClient(server.api_url).upsert_by_key(SET, {"contoso_assetcode": "X"}, {}, mode="merge")


# ---- $batch ----------------------------------------------------------------
def test_changeset_rolls_back_and_reports_index(server):
    server.fake.fail_on_names.add("BAD")
    client = DataverseClient(server.api_url)
    rows = [{"contoso_assetcode": "R-1", "contoso_name": "ok"},
            {"contoso_assetcode": "R-2", "contoso_name": "ok"},
            {"contoso_assetcode": "R-3", "contoso_name": "BAD"},
            {"contoso_assetcode": "R-4", "contoso_name": "ok"}]
    with pytest.raises(BatchError) as ei:
        client.batch_create(SET, rows)
    assert ei.value.index == 2
    assert server.fake.count() == 0, "change set must be atomic"


def test_batch_is_single_request_with_changeset(server):
    client = DataverseClient(server.api_url)
    client.batch_create(SET, [{"contoso_assetcode": f"S-{i}", "contoso_name": "v"} for i in range(5)])
    posts = [r for r in server.fake.requests if r["method"] == "POST"]
    assert len(posts) == 1 and posts[0]["target"].endswith("/$batch")
    assert server.fake.count() == 5


def test_batch_empty_and_oversize(server):
    client = DataverseClient(server.api_url)
    assert client.batch_create(SET, []) == []
    assert server.fake.requests == []
    with pytest.raises(ValueError):
        client.batch_create(SET, [{"contoso_name": "x"}] * 1001)


def test_batch_retries_on_429(server, sleeps):
    server.fake.throttle(1, retry_after=3)
    ids = DataverseClient(server.api_url).batch_create(SET, [{"contoso_assetcode": "T-1", "contoso_name": "v"}])
    assert len(ids) == 1 and sleeps


# ---- change tracking -------------------------------------------------------
def test_delta_returns_updates_and_deletes(server):
    ids = server.fake.seed(5)
    client = DataverseClient(server.api_url)
    store = TokenStore()
    mirror = {}
    client.sync_changes(SET, COLS, store, lambda r: mirror.__setitem__(r["contoso_assetid"], r),
                        lambda i: mirror.pop(i, None))
    assert len(mirror) == 5
    server.fake.update_row(ids[0], {"contoso_name": "Renamed"})
    server.fake.delete_row(ids[1])
    server.fake.create({"contoso_assetcode": "NEW-1", "contoso_name": "New"})
    first_link = store.delta_link
    stats = client.sync_changes(SET, COLS, store, lambda r: mirror.__setitem__(r["contoso_assetid"], r),
                                lambda i: mirror.pop(i, None))
    assert stats == {"upserts": 2, "deletes": 1}
    assert ids[1] not in mirror
    assert mirror[ids[0]]["contoso_name"] == "Renamed"
    assert len(mirror) == 5
    assert store.delta_link != first_link
    delta_get = _gets(server)[-1]
    assert "$deltatoken=" in delta_get["target"]
    assert delta_get["target"] == first_link[len(server.base_url):], "use the stored deltaLink verbatim"


def test_no_changes_is_a_noop_with_new_link(server):
    server.fake.seed(2)
    client = DataverseClient(server.api_url)
    store = TokenStore()
    client.sync_changes(SET, COLS, store, lambda r: None, lambda i: None)
    stats = client.sync_changes(SET, COLS, store, lambda r: None, lambda i: None)
    assert stats == {"upserts": 0, "deletes": 0}
    assert len(store.saves) == 2


def test_token_saved_only_after_all_pages(server):
    server.fake.seed(7)
    client = DataverseClient(server.api_url)
    store = TokenStore()
    applied = []

    def boom(row):
        applied.append(row)
        if len(applied) == 5:
            raise RuntimeError("downstream DB down")

    with pytest.raises(RuntimeError):
        client.sync_changes(SET, COLS, store, boom, lambda i: None, page_size=3)
    assert store.delta_link is None and store.saves == [], "a half-applied sync must not advance the token"
    # retry from scratch works and drains all pages
    seen = []
    client.sync_changes(SET, COLS, store, seen.append, lambda i: None, page_size=3)
    assert len(seen) == 7 and len(store.saves) == 1


def test_track_changes_header_and_paging(server):
    server.fake.seed(5)
    client = DataverseClient(server.api_url)
    store = TokenStore()
    client.sync_changes(SET, COLS, store, lambda r: None, lambda i: None, page_size=2)
    gets = _gets(server)
    assert len(gets) == 3
    assert "odata.track-changes" in gets[0]["headers"].get("prefer", "")
    assert len(store.saves) == 1
