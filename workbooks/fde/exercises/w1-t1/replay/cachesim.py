"""A prompt-cache simulator with the Messages API's prefix semantics. Given; not the bug.

The cache key is the exact bytes of the request prefix in API order: tools, then system
blocks, then message blocks. A request writes an entry at each ``cache_control``
breakpoint; a later request reads the longest prefix that ends at an entry still alive
(TTL 5 minutes, refreshed on read). ``cache_control`` markers themselves are not part of
the key. Token counts are approximated as characters / 4.

The cache is shared by every worker of an organization, as the real one is.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

TTL_SECONDS = 300


def _strip(block: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in block.items() if k != "cache_control"}


def segments(request: dict[str, Any]) -> list[tuple[str, bool]]:
    """(canonical bytes, is_breakpoint) for every block, in prefix order."""
    out: list[tuple[str, bool]] = []
    for tool in request.get("tools") or []:
        out.append(("tool:" + json.dumps(_strip(tool), sort_keys=True), "cache_control" in tool))
    system = request.get("system") or []
    if isinstance(system, str):
        system = [{"type": "text", "text": system}]
    for block in system:
        out.append(("system:" + json.dumps(_strip(block), sort_keys=True), "cache_control" in block))
    for message in request.get("messages") or []:
        content = message["content"]
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
        for block in blocks:
            out.append(
                (f"{message['role']}:" + json.dumps(_strip(block), sort_keys=True), "cache_control" in block)
            )
    return out


@dataclass
class Usage:
    input_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int


@dataclass
class PromptCache:
    ttl: float = TTL_SECONDS
    entries: dict[str, float] = field(default_factory=dict)  # prefix hash -> expires at

    def call(self, request: dict[str, Any], now: float) -> Usage:
        segs = segments(request)
        h = hashlib.sha256()
        hashes: list[str] = []
        cumulative: list[int] = []
        total = 0
        for text, _ in segs:
            h.update(text.encode())
            hashes.append(h.hexdigest())
            total += max(1, len(text) // 4)
            cumulative.append(total)
        breakpoints = [i for i, (_, bp) in enumerate(segs) if bp]
        last_bp = breakpoints[-1] if breakpoints else -1
        read_upto = -1
        for i in range(last_bp, -1, -1):
            expires = self.entries.get(hashes[i])
            if expires is not None and expires > now:
                read_upto = i
                self.entries[hashes[i]] = now + self.ttl
                break
        for i in breakpoints:
            self.entries[hashes[i]] = now + self.ttl
        read = cumulative[read_upto] if read_upto >= 0 else 0
        cached_span = cumulative[last_bp] if last_bp >= 0 else 0
        return Usage(
            input_tokens=total - cached_span,
            cache_read_input_tokens=read,
            cache_creation_input_tokens=cached_span - read,
        )
