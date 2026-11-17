"""Hidden checks for w6-c1."""

from __future__ import annotations

import copy

import pytest
from botocore.stub import ANY
from w6c1_hidden_support import URL, body, event, ok_anonymous, ok_registered

from embed.handler import ConfigError, handler, load_config, validate_domains, validate_lifetime


@pytest.fixture
def cfg():
    return load_config()


def anon_params(tenant, ids, initial):
    return {"AwsAccountId": "111122223333", "SessionLifetimeInMinutes": ANY, "AllowedDomains": ANY,
            "Namespace": "default",
            "AuthorizedResourceArns": [f"arn:aws:quicksight:us-east-1:111122223333:dashboard/{i}" for i in ids],
            "ExperienceConfiguration": {"Dashboard": {"InitialDashboardId": initial}},
            "SessionTags": [{"Key": "tenant_id", "Value": tenant}]}


def test_anonymous_tag_and_arns_come_from_claim_only(qs, cfg):
    qs.stub.add_response("generate_embed_url_for_anonymous_user", ok_anonymous(),
                         anon_params("delta-outfitters", ["dash-shared-ops"], "dash-shared-ops"))
    ev = event(tenant="delta-outfitters", user=None)
    ev["queryStringParameters"] = {"tenant_id": "brightline-health"}
    assert handler(ev, client=qs.client, cfg=cfg)["statusCode"] == 200


def test_anonymous_requested_dashboard_must_be_authorized(qs, cfg):
    r = handler(event(tenant="delta-outfitters", user=None, dashboard="dash-shared-sla"), client=qs.client, cfg=cfg)
    assert r["statusCode"] == 404


def test_anonymous_requested_dashboard_ok(qs, cfg):
    qs.stub.add_response("generate_embed_url_for_anonymous_user", ok_anonymous(),
                         anon_params("brightline-health", ["dash-shared-ops", "dash-shared-sla"], "dash-shared-sla"))
    assert handler(event(tenant="brightline-health", user=None, dashboard="dash-shared-sla"),
                   client=qs.client, cfg=cfg)["statusCode"] == 200


def test_registered_other_tenants_dashboard_404(qs, cfg):
    assert handler(event(dashboard="dash-corvid-ops"), client=qs.client, cfg=cfg)["statusCode"] == 404


def test_registered_uses_tenant_namespace(qs, cfg):
    qs.stub.add_response("generate_embed_url_for_registered_user", ok_registered(),
                         {"AwsAccountId": "111122223333", "SessionLifetimeInMinutes": ANY, "AllowedDomains": ANY,
                          "UserArn": "arn:aws:quicksight:us-east-1:111122223333:user/corvid-logistics/sam.k",
                          "ExperienceConfiguration": {"Dashboard": {"InitialDashboardId": "dash-corvid-ops"}}})
    assert handler(event(tenant="corvid-logistics", user="sam.k"), client=qs.client, cfg=cfg)["statusCode"] == 200


def test_registered_bad_username_403(qs, cfg):
    assert handler(event(user="a/../b"), client=qs.client, cfg=cfg)["statusCode"] == 403
    assert handler(event(user=None), client=qs.client, cfg=cfg)["statusCode"] == 403


def test_no_tenant_or_unknown_tenant_403(qs, cfg):
    assert handler(event(tenant=None), client=qs.client, cfg=cfg)["statusCode"] == 403
    assert handler(event(tenant="evil-corp"), client=qs.client, cfg=cfg)["statusCode"] == 403


def test_user_not_found_is_actionable_403(qs, cfg):
    qs.stub.add_client_error("generate_embed_url_for_registered_user", "QuickSightUserNotFoundException",
                             "user not found", 404)
    r = handler(event(), client=qs.client, cfg=cfg)
    assert r["statusCode"] == 403 and "namespace" in body(r)["error"].lower()


def test_throttling_is_503_with_retry_after(qs, cfg):
    qs.stub.add_client_error("generate_embed_url_for_registered_user", "ThrottlingException", "slow down", 429)
    r = handler(event(), client=qs.client, cfg=cfg)
    assert r["statusCode"] == 503 and "retry-after" in {k.lower() for k in r["headers"]}


def test_pricing_plan_error_mapped(qs, cfg):
    qs.stub.add_client_error("generate_embed_url_for_anonymous_user", "UnsupportedPricingPlanException", "no", 403)
    r = handler(event(tenant="delta-outfitters", user=None), client=qs.client, cfg=cfg)
    assert r["statusCode"] >= 500 and "capacity" in body(r)["error"].lower()


def test_no_store_on_every_response(qs, cfg):
    qs.stub.add_response("generate_embed_url_for_registered_user", ok_registered())
    for r in (handler(event(), client=qs.client, cfg=cfg), handler(event(tenant=None), client=qs.client, cfg=cfg)):
        assert {k.lower(): v for k, v in r["headers"].items()}.get("cache-control") == "no-store"


def test_url_never_logged(qs, cfg, caplog):
    qs.stub.add_response("generate_embed_url_for_registered_user", ok_registered())
    with caplog.at_level("DEBUG"):
        handler(event(), client=qs.client, cfg=cfg)
    assert "SECRETCODE" not in caplog.text and URL not in caplog.text


@pytest.mark.parametrize("bad", [
    [], ["http://app.tidewater.example"], ["https://app.tidewater.example/"], ["https://app.tidewater.example/embed"],
    ["https://a.example", "https://b.example", "https://c.example", "https://d.example"], ["app.tidewater.example"],
])
def test_bad_domains_rejected(bad):
    with pytest.raises(ConfigError):
        validate_domains(bad)


def test_good_domains_accepted():
    assert validate_domains(["https://app.tidewater.example", "https://*.portal.tidewater.example",
                             "https://staging.tidewater.example:8443"])


@pytest.mark.parametrize("bad", [0, 14, 601, "60", 1.5, True])
def test_bad_lifetime_rejected(bad):
    with pytest.raises(ConfigError):
        validate_lifetime(bad)


def test_lifetime_bounds_ok():
    assert validate_lifetime(15) == 15 and validate_lifetime(600) == 600


def test_load_config_rejects_bad_file(tmp_path):
    import json
    import pathlib
    src = json.loads((pathlib.Path(__file__).resolve().parent.parent / "embed" / "tenants.json").read_text())
    bad = copy.deepcopy(src)
    bad["session_lifetime_minutes"] = 720
    p = tmp_path / "t.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(ConfigError):
        load_config(p)
