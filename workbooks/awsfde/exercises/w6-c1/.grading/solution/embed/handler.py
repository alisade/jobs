"""Embed-URL Lambda (HTTP API payload 2.0, Cognito JWT authorizer).

GET /analytics/embed-url?dashboard=<id>   ->   {"embedUrl": "..."}

Registered tenants (one Quick Sight namespace per tenant, user-based RLS):
  GenerateEmbedUrlForRegisteredUser with the caller's user ARN in the tenant's namespace.
Anonymous tenants (capacity pricing, tag-based RLS):
  GenerateEmbedUrlForAnonymousUser in the default namespace with a tenant_id session tag and
  AuthorizedResourceArns limited to that tenant's dashboards.
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
from typing import Any

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger("tidewater.embed")
CONFIG_PATH = pathlib.Path(__file__).resolve().parent / "tenants.json"
DOMAIN_RE = re.compile(r"^https://(\*\.)?[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+(:[0-9]{1,5})?$")
USER_RE = re.compile(r"^[A-Za-z0-9+=,.@_-]{1,128}$")


class ConfigError(ValueError):
    pass


def validate_domains(domains: list[str]) -> list[str]:
    """https origins only (scheme + host [+ port], no path), optional *. subdomain wildcard, 1-3 per call."""
    if not domains or len(domains) > 3:
        raise ConfigError("AllowedDomains takes one to three domains per call")
    for d in domains:
        if not isinstance(d, str) or not DOMAIN_RE.match(d):
            raise ConfigError(f"not an https origin: {d!r}")
    return list(domains)


def validate_lifetime(minutes: int) -> int:
    if not isinstance(minutes, int) or isinstance(minutes, bool) or not 15 <= minutes <= 600:
        raise ConfigError("SessionLifetimeInMinutes must be an integer from 15 to 600")
    return minutes


def load_config(path: pathlib.Path = CONFIG_PATH) -> dict:
    cfg = json.loads(path.read_text())
    validate_domains(cfg["allowed_domains"])
    validate_lifetime(cfg["session_lifetime_minutes"])
    return cfg


def _resp(code: int, body: dict, extra: dict | None = None) -> dict:
    headers = {"content-type": "application/json", "cache-control": "no-store"}
    headers.update(extra or {})
    return {"statusCode": code, "headers": headers, "body": json.dumps(body)}


def _claims(event: dict) -> dict:
    return (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}


def dashboard_arn(cfg: dict, dashboard_id: str) -> str:
    return f"arn:aws:quicksight:{cfg['region']}:{cfg['account_id']}:dashboard/{dashboard_id}"


def build_request(cfg: dict, claims: dict, requested: str | None) -> tuple[str, dict]:
    """(operation, kwargs) for the caller. Raises PermissionError / LookupError for 403 / 404."""
    tenant = claims.get("tenant_id")
    if not tenant:
        raise PermissionError("no tenant in token")
    t = cfg["tenants"].get(tenant)
    if t is None:
        raise PermissionError("tenant has no analytics configured")
    common = {"AwsAccountId": cfg["account_id"], "SessionLifetimeInMinutes": cfg["session_lifetime_minutes"],
              "AllowedDomains": list(cfg["allowed_domains"])}
    if t["mode"] == "registered":
        if requested not in (None, t["dashboard_id"]):
            raise LookupError("dashboard not available")
        user = claims.get("cognito:username") or claims.get("username")
        if not user or not USER_RE.match(user):
            raise PermissionError("no usable user name in token")
        return "generate_embed_url_for_registered_user", {
            **common,
            "UserArn": f"arn:aws:quicksight:{cfg['region']}:{cfg['account_id']}:user/{t['namespace']}/{user}",
            "ExperienceConfiguration": {"Dashboard": {"InitialDashboardId": t["dashboard_id"]}},
        }
    if t["mode"] == "anonymous":
        ids = t["dashboard_ids"]
        initial = requested or ids[0]
        if initial not in ids:
            raise LookupError("dashboard not available")
        return "generate_embed_url_for_anonymous_user", {
            **common,
            "Namespace": "default",
            "AuthorizedResourceArns": [dashboard_arn(cfg, i) for i in ids],
            "ExperienceConfiguration": {"Dashboard": {"InitialDashboardId": initial}},
            "SessionTags": [{"Key": "tenant_id", "Value": tenant}],
        }
    raise ConfigError(f"unknown mode {t['mode']!r}")


ERRORS = {
    "QuickSightUserNotFoundException": (403, "Your analytics user is not provisioned yet. Ask your admin to add you to the tenant's Quick Sight namespace."),
    "ResourceNotFoundException": (404, "Dashboard not found."),
    "UnsupportedPricingPlanException": (500, "Anonymous embedding needs capacity pricing on the Quick Sight account."),
    "UnsupportedUserEditionException": (500, "Embedding needs Quick Sight Enterprise edition."),
    "SessionLifetimeInMinutesInvalidException": (500, "Embedding session lifetime misconfigured."),
    "AccessDeniedException": (500, "The embedding role is not allowed to generate this URL."),
}


def handler(event: dict, context: Any = None, client: Any = None, cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    claims = _claims(event)
    requested = (event.get("queryStringParameters") or {}).get("dashboard")
    try:
        op, kwargs = build_request(cfg, claims, requested)
    except PermissionError as e:
        return _resp(403, {"error": str(e)})
    except LookupError as e:
        return _resp(404, {"error": str(e)})
    client = client or boto3.client("quicksight", region_name=cfg["region"])
    try:
        out = getattr(client, op)(**kwargs)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "ThrottlingException":
            return _resp(503, {"error": "Analytics is busy, retry shortly."}, {"retry-after": "2"})
        status, msg = ERRORS.get(code, (500, "Could not open the dashboard."))
        log.error(json.dumps({"event": "embed_error", "tenant_id": claims.get("tenant_id"), "code": code,
                              "request_id": e.response.get("ResponseMetadata", {}).get("RequestId")}))
        return _resp(status, {"error": msg, "code": code})
    log.info(json.dumps({"event": "embed_url_issued", "tenant_id": claims.get("tenant_id"), "operation": op,
                         "request_id": out.get("RequestId")}))
    return _resp(200, {"embedUrl": out["EmbedUrl"]})
