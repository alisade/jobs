"""Keyset pagination for GET /v1/contacts."""

from __future__ import annotations

import base64

from sqlalchemy import select

from .db import contacts
from .problems import Problem

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def encode_cursor(row) -> str:
    return base64.urlsafe_b64encode(row.created_at.encode()).decode()


def decode_cursor(cursor: str) -> str:
    return base64.urlsafe_b64decode(cursor.encode()).decode()


def page_query(tenant_id: str, cursor: str | None, limit: int):
    q = select(contacts).where(contacts.c.tenant_id == tenant_id)
    if cursor:
        after = decode_cursor(cursor)
        q = q.where(contacts.c.created_at > after)
    return q.order_by(contacts.c.created_at).limit(limit)


def clamp_limit(limit: int | None) -> int:
    return limit or DEFAULT_LIMIT
