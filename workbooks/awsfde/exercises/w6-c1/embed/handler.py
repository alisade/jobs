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
    """TODO: https origins only (scheme + host [+ port], no path, no trailing slash), optional *. subdomain wildcard, one to three per call (the API limit). Raise ConfigError."""
    raise NotImplementedError



def validate_lifetime(minutes: int) -> int:
    """TODO: SessionLifetimeInMinutes is an integer from 15 to 600. Raise ConfigError."""
    raise NotImplementedError



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
    """TODO: (operation name, kwargs) for the caller; see README. PermissionError -> 403, LookupError -> 404."""
    raise NotImplementedError



ERRORS = {
    "QuickSightUserNotFoundException": (403, "Your analytics user is not provisioned yet. Ask your admin to add you to the tenant's Quick Sight namespace."),
    "ResourceNotFoundException": (404, "Dashboard not found."),
    "UnsupportedPricingPlanException": (500, "Anonymous embedding needs capacity pricing on the Quick Sight account."),
    "UnsupportedUserEditionException": (500, "Embedding needs Quick Sight Enterprise edition."),
    "SessionLifetimeInMinutesInvalidException": (500, "Embedding session lifetime misconfigured."),
    "AccessDeniedException": (500, "The embedding role is not allowed to generate this URL."),
}


def handler(event: dict, context: Any = None, client: Any = None, cfg: dict | None = None) -> dict:
    """TODO: build the request, call Quick Sight, map errors (ERRORS, plus ThrottlingException -> 503 with retry-after), never log the URL, always cache-control: no-store."""
    raise NotImplementedError
