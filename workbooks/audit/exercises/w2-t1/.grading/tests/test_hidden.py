"""Hidden tests for audit/w2-t1."""

from __future__ import annotations

import pytest

from popexport import client, population
from popexport.fakeapi import FakeGitHub


def fake_pulls(n):
    return [{"number": i, "state": "closed", "base": {"ref": "main"}, "title": f"CHG-{300000 + i} x", "user": {"login": "a"},
             "created_at": "2026-02-01T00:00:00Z", "updated_at": f"2026-02-01T00:{i // 60 % 60:02d}:{i % 60:02d}Z",
             "merged_at": "2026-02-01T00:00:00Z", "closed_at": "2026-02-01T00:00:00Z"} for i in range(1, n + 1)]


@pytest.mark.parametrize("cap,per_page", [(50, 100), (30, 100), (100, 100), (50, 20), (7, 50)])
def test_every_pull_is_fetched(cap, per_page):
    api = FakeGitHub(max_per_page=cap)
    got = client.fetch_closed_pulls(api, "mfh/tms-core", per_page=per_page)
    assert len(got) == 488
    assert len({p["number"] for p in got}) == 488


def test_request_count_matches_pages():
    api = FakeGitHub(max_per_page=50)
    client.fetch_closed_pulls(api, "mfh/tms-core")
    assert len(api.calls) == 10


def test_exact_multiple_of_page_size():
    api = FakeGitHub(max_per_page=50, pulls=fake_pulls(100))
    got = client.fetch_closed_pulls(api, "mfh/tms-core", per_page=50)
    assert len(got) == 100 and len(api.calls) == 2


def test_empty_repository():
    api = FakeGitHub(pulls=[])
    assert client.fetch_closed_pulls(api, "mfh/tms-core") == []


def test_pagination_loop_is_bounded():
    api = FakeGitHub(max_per_page=50, broken_next=True)
    with pytest.raises(Exception):
        client.fetch_closed_pulls(api, "mfh/tms-core")
    assert len(api.calls) <= 20


def test_full_reconciliation_numbers():
    res = population.build(client.fetch_closed_pulls(FakeGitHub(), "mfh/tms-core"))
    assert res["population"] == 421 and res["deploy_log_changes"] == 421 and res["missing_from_population"] == 0


def test_time_zone_logic_unchanged():
    """Guard: the period filter was correct all along."""
    from datetime import date
    assert population.local_date("2026-01-01T05:30:00Z") == date(2025, 12, 31)
    assert population.local_date("2026-07-01T04:30:00Z") == date(2026, 6, 30)
