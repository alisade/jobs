"""GET /api/analytics/embed-url - mints a Quick Sight embed URL for the caller (release 2026.11.05)."""

from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger("tidewater.embed")

ACCOUNT = "111122223333"
ALLOWED_DOMAINS = ["https://app.tidewater.example", "https://*.portal.tidewater.example"]
SESSION_LIFETIME_MINUTES = 15
TENANTS = {
    "acme-foods": {"mode": "registered", "namespace": "acme-foods", "dashboard_id": "dash-ops"},
    "corvid-logistics": {"mode": "registered", "namespace": "corvid-logistics", "dashboard_id": "dash-ops"},
    "brightline-health": {"mode": "anonymous", "dashboard_ids": ["dash-ops"]},
    "delta-outfitters": {"mode": "anonymous", "dashboard_ids": ["dash-ops"]},
}


def handler(event: dict, client: Any) -> dict:
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    tenant = claims.get("tenant_id")
    t = TENANTS.get(tenant or "")
    if not t:
        return {"statusCode": 403, "headers": {"content-type": "application/json"}, "body": json.dumps({"error": "forbidden"})}
    common = {"AwsAccountId": ACCOUNT, "SessionLifetimeInMinutes": SESSION_LIFETIME_MINUTES, "AllowedDomains": ALLOWED_DOMAINS}
    if t["mode"] == "registered":
        out = client.generate_embed_url_for_registered_user(
            **common, UserArn=f"arn:aws:quicksight:us-east-1:{ACCOUNT}:user/{t['namespace']}/{claims['username']}",
            ExperienceConfiguration={"Dashboard": {"InitialDashboardId": t["dashboard_id"]}})
    else:
        out = client.generate_embed_url_for_anonymous_user(
            **common, Namespace="default",
            AuthorizedResourceArns=[f"arn:aws:quicksight:us-east-1:{ACCOUNT}:dashboard/{d}" for d in t["dashboard_ids"]],
            ExperienceConfiguration={"Dashboard": {"InitialDashboardId": t["dashboard_ids"][0]}},
            SessionTags=[{"Key": "tenant_id", "Value": tenant}])
    log.info(json.dumps({"event": "embed_url_issued", "tenant_id": tenant, "request_id": out["RequestId"]}))
    return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps({"embedUrl": out["EmbedUrl"]})}
