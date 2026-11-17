"""Keyset pagination for GET /v1/contacts.

The sort key must be unique and stable: (created_at, id). The cursor carries both values of the last
row, encoded as opaque base64url JSON, and the next page starts strictly after that pair.
"""

from __future__ import annotations

import base64
import binascii
import json

from sqlalchemy import and_, or_, select

from .db import contacts
from .problems import Problem

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def encode_cursor(row) -> str:
    raw = json.dumps({"c": row.created_at, "i": row.id}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[str, str]:
    try:
        pad = "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode((cursor + pad).encode()))
        c, i = data["c"], data["i"]
        if not isinstance(c, str) or not isinstance(i, str):
            raise ValueError("bad types")
        return c, i
    except (binascii.Error, ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise Problem(400, "invalid-cursor", "The cursor is not valid",
                      "Pass back next_cursor exactly as returned by the previous page.") from exc


def page_query(tenant_id: str, cursor: str | None, limit: int):
    q = select(contacts).where(contacts.c.tenant_id == tenant_id)
    if cursor:
        c, i = decode_cursor(cursor)
        # row-value comparison (created_at, id) > (c, i), written out so every engine plans it well
        q = q.where(or_(contacts.c.created_at > c, and_(contacts.c.created_at == c, contacts.c.id > i)))
    return q.order_by(contacts.c.created_at, contacts.c.id).limit(limit)


def clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    if limit < 1:
        raise Problem(400, "invalid-limit", "limit must be between 1 and 200")
    return min(limit, MAX_LIMIT)
