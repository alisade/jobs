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


class IdentityError(ValueError):
    """The verified claims do not carry a usable tenant or subject."""


def actor_id(claims: dict) -> str:
    """TODO: "<tenant_id>:<sub>" from the VERIFIED claims. Raise IdentityError when tenant_id or sub
    is missing, or tenant_id does not match TENANT_RE (custom namespace values must be lowercase)."""
    raise NotImplementedError


def namespace(claims: dict) -> str:
    """TODO: the resolved long-term namespace for this caller, normalized with a leading and a
    trailing slash: /tenant/<tenant_id>/actor/<actor_id>/preferences/"""
    raise NotImplementedError


def recall(client: Any, memory_id: str, claims: dict, query: str, top_k: int = 5) -> list[str]:
    """TODO: RetrieveMemoryRecords in this caller's namespace only; return the record texts."""
    raise NotImplementedError


def remember(client: Any, memory_id: str, claims: dict, session_id: str, user_text: str,
             assistant_text: str, now: dt.datetime) -> str:
    """TODO: one CreateEvent with the USER and ASSISTANT turns (conversational payload), the caller's
    actorId and sessionId, and extractionConfig.namespaceVariables {"tenantid": <tenant_id>}.
    Return the eventId."""
    raise NotImplementedError
