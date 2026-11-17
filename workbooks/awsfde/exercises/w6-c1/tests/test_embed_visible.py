"""Visible checks for w6-c1 (happy paths). The grader runs more."""

from w6c1_support import body, event, ok_anonymous, ok_registered

from embed.handler import handler, load_config


def test_registered_tenant(qs):
    qs.stub.add_response("generate_embed_url_for_registered_user", ok_registered(), {
        "AwsAccountId": "111122223333", "SessionLifetimeInMinutes": 60,
        "AllowedDomains": ["https://app.tidewater.example", "https://*.portal.tidewater.example"],
        "UserArn": "arn:aws:quicksight:us-east-1:111122223333:user/acme-foods/maria.lopez",
        "ExperienceConfiguration": {"Dashboard": {"InitialDashboardId": "dash-acme-ops"}}})
    r = handler(event(), client=qs.client, cfg=load_config())
    assert r["statusCode"] == 200 and body(r)["embedUrl"].startswith("https://")


def test_anonymous_tenant(qs):
    qs.stub.add_response("generate_embed_url_for_anonymous_user", ok_anonymous(), {
        "AwsAccountId": "111122223333", "SessionLifetimeInMinutes": 60,
        "AllowedDomains": ["https://app.tidewater.example", "https://*.portal.tidewater.example"],
        "Namespace": "default",
        "AuthorizedResourceArns": ["arn:aws:quicksight:us-east-1:111122223333:dashboard/dash-shared-ops",
                                   "arn:aws:quicksight:us-east-1:111122223333:dashboard/dash-shared-sla"],
        "ExperienceConfiguration": {"Dashboard": {"InitialDashboardId": "dash-shared-ops"}},
        "SessionTags": [{"Key": "tenant_id", "Value": "brightline-health"}]})
    r = handler(event(tenant="brightline-health", user=None), client=qs.client, cfg=load_config())
    assert r["statusCode"] == 200
