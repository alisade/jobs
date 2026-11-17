"""A google.genai stand-in that simulates Gemini implicit context caching. Complete; not the bug.

Implicit caching (on by default for current Gemini models) gives a discount on input tokens when a
request starts with the same prefix as a recent request to the same model. The simulator:

  * serializes a request in the order the model sees it: tool declarations, then the system
    instruction, then the contents (serialize_request below);
  * finds the longest common prefix (in characters) with any earlier request to the same model;
  * counts tokens as characters // 4, and reports cached_content_token_count = that prefix in tokens
    when it is at least MIN_CACHE_TOKENS, else 0;
  * reports a latency that grows with the uncached input.

The prefix store can be shared between processes through a JSON file (like the server-side cache
is shared by every instance of the Function app).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google.genai import types

MIN_CACHE_TOKENS = 1024


def _text_of(contents: Any) -> str:
    out = []
    for c in contents or []:
        if isinstance(c, str):
            out.append(c)
            continue
        for p in c.parts or []:
            if p.text:
                out.append(p.text)
            elif p.function_response:
                out.append(json.dumps(p.function_response.response, sort_keys=True))
            elif p.function_call:
                out.append(json.dumps({"call": p.function_call.name, "args": p.function_call.args}, sort_keys=True))
    return "\n".join(out)


def serialize_tools(config: Any) -> str:
    decls = []
    for t in (getattr(config, "tools", None) or []):
        for d in (t.function_declarations or []):
            decls.append(d.model_dump(mode="json", exclude_none=True))
    return json.dumps(decls, sort_keys=True)


def serialize_request(contents: Any, config: Any) -> str:
    system = getattr(config, "system_instruction", None) or ""
    if not isinstance(system, str):
        system = _text_of([system])
    return "[TOOLS]" + serialize_tools(config) + "\n[SYSTEM]" + system + "\n[CONTENTS]" + _text_of(contents)


def tokens(text: str) -> int:
    return len(text) // 4


def _lcp(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


class _Models:
    def __init__(self, store: Path | None, reply: str):
        self.store = store
        self.reply = reply
        self.seen: dict[str, list[str]] = {}
        self.requests: list[dict] = []
        if store and store.exists():
            self.seen = json.loads(store.read_text())

    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> types.GenerateContentResponse:
        text = serialize_request(contents, config)
        prev = self.seen.setdefault(model, [])
        best = max((_lcp(text, p) for p in prev), default=0)
        cached = tokens(text[:best]) if tokens(text[:best]) >= MIN_CACHE_TOKENS else 0
        prev.append(text)
        del prev[:-50]
        if self.store:
            self.store.write_text(json.dumps(self.seen))
        prompt = tokens(text)
        latency = 180 + 0.12 * (prompt - cached)
        self.requests.append({"model": model, "serialized": text, "config": config, "contents": contents})
        return types.GenerateContentResponse.model_validate({
            "candidates": [{"content": {"role": "model", "parts": [{"text": self.reply}]}, "finish_reason": "STOP"}],
            "usage_metadata": {"prompt_token_count": prompt, "cached_content_token_count": cached,
                               "candidates_token_count": 110, "total_token_count": prompt + 110},
            "model_version": model,
            "sdk_http_response": {"headers": {"x-simulated-latency-ms": str(int(latency))}},
        })


class CachingFakeClient:
    def __init__(self, store: str | Path | None = None, reply: str = '{"status": "ok"}'):
        self.models = _Models(Path(store) if store else None, reply)
