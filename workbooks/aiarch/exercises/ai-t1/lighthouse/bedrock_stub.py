"""A stub of Bedrock Converse prompt caching (works as shipped).

The request prefix is read in order: toolConfig.tools, then system blocks, then message
content. Everything up to the LAST cachePoint block is the cacheable prefix. If that prefix has
at least MIN_TOKENS tokens it is cached: an identical prefix within TTL seconds of the last
use is a cache read (and refreshes the TTL); otherwise it is a cache write. Tokens are
approximated as len(json text) // 4. The clock is injected so tests are deterministic.
"""
from __future__ import annotations

import hashlib
import json
from typing import Callable

MIN_TOKENS = 1024
TTL = 300
PRICES = {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00}  # USD per million (fictional)


def _tokens(obj) -> int:
    return len(json.dumps(obj, sort_keys=True)) // 4


class FakeConverse:
    def __init__(self, clock: Callable[[], float]):
        self.clock = clock
        self.cache: dict[str, float] = {}
        self.requests: list[dict] = []

    def converse(self, modelId: str, messages: list, system: list | None = None, toolConfig: dict | None = None,
                 inferenceConfig: dict | None = None) -> dict:
        req = {"modelId": modelId, "messages": messages, "system": system or [], "toolConfig": toolConfig or {}}
        self.requests.append(json.loads(json.dumps(req)))
        segments = list((toolConfig or {}).get("tools", [])) + list(system or [])
        for m in messages:
            segments += list(m.get("content", []))
        last = max((i for i, s in enumerate(segments) if "cachePoint" in s), default=-1)
        prefix, rest = segments[: last + 1], segments[last + 1:]
        p_tok, r_tok = _tokens(prefix), _tokens(rest)
        usage = {"inputTokens": r_tok, "outputTokens": 150, "cacheReadInputTokens": 0, "cacheWriteInputTokens": 0}
        now = self.clock()
        if last >= 0 and p_tok >= MIN_TOKENS:
            key = hashlib.sha256(json.dumps(prefix, sort_keys=True).encode()).hexdigest()
            seen = self.cache.get(key)
            if seen is not None and now - seen <= TTL:
                usage["cacheReadInputTokens"] = p_tok
            else:
                usage["cacheWriteInputTokens"] = p_tok
            self.cache[key] = now
        else:
            usage["inputTokens"] += p_tok
        usage["totalTokens"] = usage["inputTokens"] + usage["cacheReadInputTokens"] + usage["cacheWriteInputTokens"] + 150
        return {"output": {"message": {"role": "assistant", "content": [{"text": "ok"}]}}, "stopReason": "end_turn",
                "usage": usage}


def cost_usd(usage: dict) -> float:
    return (usage["inputTokens"] * PRICES["input"] + usage["cacheWriteInputTokens"] * PRICES["cache_write"]
            + usage["cacheReadInputTokens"] * PRICES["cache_read"] + usage["outputTokens"] * PRICES["output"]) / 1e6
