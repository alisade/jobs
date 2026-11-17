"""AgentCore Memory: short-term events per session, long-term preference records per tenant + user.

Scheme (also in config.json):
- actorId   = "<tenant_id>:<sub>"   e.g. "acme-foods:7f3a9c2e-0b1d-4c55-9e0a-2a1b3c4d5e6f"
- long-term records live in the strategy namespace template
      /tenant/{tenantid}/actor/{actorId}/preferences/
  where {tenantid} is a custom namespace variable supplied on every CreateEvent
  (extractionConfig.namespaceVariables) and {actorId} is the event's actorId.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
SUB_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-_]{0,127}$")


class IdentityError(ValueError):
    """The verified claims do not carry a usable tenant or subject."""


def _tenant_and_sub(claims: dict) -> tuple[str, str]:
    tenant = claims.get("tenant_id")
    sub = claims.get("sub")
    if not isinstance(tenant, str) or not TENANT_RE.match(tenant):
        raise IdentityError("token has no valid tenant_id claim")
    if not isinstance(sub, str) or not SUB_RE.match(sub):
        raise IdentityError("token has no valid sub claim")
    return tenant, sub


def actor_id(claims: dict) -> str:
    tenant, sub = _tenant_and_sub(claims)
    return f"{tenant}:{sub}"


def namespace(claims: dict) -> str:
    tenant, _ = _tenant_and_sub(claims)
    return f"/tenant/{tenant}/actor/{actor_id(claims)}/preferences/"


def recall(client: Any, memory_id: str, claims: dict, query: str, top_k: int = 5) -> list[str]:
    resp = client.retrieve_memory_records(
        memoryId=memory_id,
        namespace=namespace(claims),
        searchCriteria={"searchQuery": query[:10000], "topK": top_k},
    )
    return [r["content"]["text"] for r in resp.get("memoryRecordSummaries", []) if r.get("content", {}).get("text")]


def remember(client: Any, memory_id: str, claims: dict, session_id: str, user_text: str,
             assistant_text: str, now: dt.datetime) -> str:
    tenant, _ = _tenant_and_sub(claims)
    resp = client.create_event(
        memoryId=memory_id,
        actorId=actor_id(claims),
        sessionId=session_id,
        eventTimestamp=now,
        payload=[
            {"conversational": {"content": {"text": user_text[:100000]}, "role": "USER"}},
            {"conversational": {"content": {"text": assistant_text[:100000]}, "role": "ASSISTANT"}},
        ],
        extractionConfig={"namespaceVariables": {"tenantid": tenant}},
    )
    return resp["event"]["eventId"]
