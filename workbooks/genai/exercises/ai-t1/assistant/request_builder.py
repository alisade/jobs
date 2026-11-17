"""Builds the Messages API request for each assistant turn.

Release 2026.11.10 refactor: tools are enabled per feature flag, and the current date and time
is given to the model so it can answer "is the store open now?".

Prompt caching: the provider caches the request prefix up to the cache_control breakpoint.
Order of the prefix is tools, then system, then messages. A cache hit needs the prefix bytes to be
identical to an earlier request.
"""

import datetime as dt
import hashlib
import json

from .tools import PRODUCT_GUIDE, SYSTEM_POLICY, TOOL_DEFS

MODEL = "claude-sonnet-4-5"
ENABLED_TOOLS = {"search_products", "check_inventory", "get_order_status", "start_return", "store_hours"}


def build_request(user_message: str, history: list[dict] | None = None, now: dt.datetime | None = None,
                  store_id: str = "web") -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    tools = [TOOL_DEFS[name] for name in ENABLED_TOOLS]
    system = [
        {"type": "text", "text": SYSTEM_POLICY},
        {"type": "text", "text": PRODUCT_GUIDE, "cache_control": {"type": "ephemeral"}},
    ]
    stamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    messages = list(history or []) + [
        {"role": "user", "content": f"[context: store {store_id}, current time {stamp}]\n{user_message}"}
    ]
    return {"model": MODEL, "max_tokens": 1024, "tools": tools, "system": system, "messages": messages}


def prefix_bytes(req: dict) -> bytes:
    """The cached prefix as the provider sees it: tools, then system blocks up to the breakpoint."""
    parts: list = [{"tools": req["tools"]}]
    for block in req["system"]:
        parts.append(block)
        if "cache_control" in block:
            break
    return json.dumps(parts, separators=(",", ":")).encode()


def prefix_hash(req: dict) -> str:
    return hashlib.sha256(prefix_bytes(req)).hexdigest()[:16]
