"""Hidden checks for w6-t1."""

from __future__ import annotations

import json
import pathlib

import replay
from api.embed_handler import handler
from edge.cloudfront import Distribution
from edge.quicksight import FakeQuickSight

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _ev(tenant, user="u1"):
    return {"requestContext": {"authorizer": {"jwt": {"claims": {"tenant_id": tenant, "username": user}}}}}


def _cc(resp):
    return {k.lower(): v for k, v in resp["headers"].items()}.get("cache-control", "")


def test_replay_clean(tmp_path):
    s = replay.run(str(tmp_path / "r"))
    assert s["blank_dashboards"] == 0 and s["views_of_another_tenants_data"] == 0


def test_no_edge_hits_on_embed_url(tmp_path):
    replay.run(str(tmp_path / "r"))
    lines = [l for l in (tmp_path / "r" / "cloudfront-access.log").read_text().splitlines() if "/api/analytics/" in l]
    assert lines and not any("\tHit\t" in l for l in lines)


def test_handler_sends_no_store_on_success_and_error():
    qs = FakeQuickSight()
    assert "no-store" in _cc(handler(_ev("acme-foods"), qs))
    assert "no-store" in _cc(handler(_ev("delta-outfitters"), qs))
    assert "no-store" in _cc(handler(_ev("nobody"), qs))


def test_embed_path_not_cacheable_even_if_origin_forgets_the_header():
    d = Distribution(ROOT / "config" / "distribution.json")
    calls = []

    def origin(p, q, h):
        calls.append(1)
        return {"statusCode": 200, "headers": {}, "body": "{}"}
    for t in (0, 1, 2):
        d.get(t, "/api/analytics/embed-url", "dashboard=dash-ops", {}, origin)
    assert len(calls) == 3, "the edge behavior itself must not cache the embed endpoint"


def test_guard_catalog_api_still_cached():
    d = Distribution(ROOT / "config" / "distribution.json")
    calls = []

    def origin(p, q, h):
        calls.append(1)
        return {"statusCode": 200, "headers": {}, "body": "[]"}
    for t in (0, 10, 20):
        d.get(t, "/api/catalog/items", "page=1", {}, origin)
    assert len(calls) == 1, "ASK-377 catalog caching must keep working"


def test_guard_static_assets_cached():
    d = Distribution(ROOT / "config" / "distribution.json")
    calls = []

    def origin(p, q, h):
        calls.append(1)
        return {"statusCode": 200, "headers": {"cache-control": "max-age=3600"}, "body": ""}
    d.get(0, "/assets/app.js", "", {}, origin)
    d.get(5, "/assets/app.js", "", {}, origin)
    assert len(calls) == 1


def test_guard_tenant_scoping_unchanged():
    qs = FakeQuickSight()
    url = json.loads(handler(_ev("delta-outfitters"), qs)["body"])["embedUrl"]
    assert qs.urls[url]["tenant"] == "delta-outfitters"
    assert handler(_ev("nobody"), qs)["statusCode"] == 403


def test_guard_distribution_ids_unchanged():
    d = json.loads((ROOT / "config" / "distribution.json").read_text())
    assert d["Id"] == "E2TIDEWATER9K"
    assert d["DefaultCacheBehavior"]["CachePolicyId"] == "658327ea-f89d-4fab-a63d-7e88639e58f6"
