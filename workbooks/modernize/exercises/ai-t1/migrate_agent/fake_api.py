"""Offline stand-in for the Messages API's prompt caching accounting (no network, no key).

Model of the real behaviour, simplified: the cacheable prefix is tools, then system blocks, then
messages, up to and including the last block carrying cache_control. If that exact prefix (byte for
byte) was written in the last 5 minutes, the request reads it (cache_read_input_tokens); otherwise it
writes it (cache_creation_input_tokens). Tokens are estimated as characters / 4. Prices are
illustrative per million tokens: input 3.00, cache write 3.75, cache read 0.30, output 15.00.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

PRICE = {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00}
TTL = timedelta(minutes=5)


def _blocks(req: dict) -> list[dict]:
    """Flatten the request into ordered blocks: tools, system, message content."""
    out: list[dict] = [{"tool": t} for t in req.get("tools", [])]
    system = req.get("system", [])
    if isinstance(system, str):
        system = [{"type": "text", "text": system}]
    out += list(system)
    for m in req.get("messages", []):
        content = m["content"] if isinstance(m["content"], list) else [{"type": "text", "text": m["content"]}]
        out += [dict(b, _role=m["role"]) for b in content]
    return out


def _tokens(blocks: list[dict]) -> int:
    return len(json.dumps(blocks, sort_keys=True)) // 4


class FakeMessagesApi:
    def __init__(self):
        self._cache: dict[str, datetime] = {}

    def usage(self, req: dict, now: datetime, output_tokens: int = 400) -> dict:
        blocks = _blocks(req)
        marks = [i for i, b in enumerate(blocks) if "cache_control" in b or "cache_control" in b.get("tool", {})]
        if not marks:
            return {"input_tokens": _tokens(blocks), "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                    "output_tokens": output_tokens}
        cut = marks[-1] + 1
        prefix, rest = blocks[:cut], blocks[cut:]
        key = hashlib.sha256(json.dumps(prefix, sort_keys=True).encode()).hexdigest()
        hit = key in self._cache and now - self._cache[key] <= TTL
        self._cache[key] = now
        p = _tokens(prefix)
        return {"input_tokens": _tokens(rest), "cache_creation_input_tokens": 0 if hit else p,
                "cache_read_input_tokens": p if hit else 0, "output_tokens": output_tokens}

    @staticmethod
    def cost(u: dict) -> float:
        return (u["input_tokens"] * PRICE["input"] + u["cache_creation_input_tokens"] * PRICE["cache_write"]
                + u["cache_read_input_tokens"] * PRICE["cache_read"] + u["output_tokens"] * PRICE["output"]) / 1e6
