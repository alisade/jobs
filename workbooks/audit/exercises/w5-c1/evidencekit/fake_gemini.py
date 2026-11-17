"""A stand-in for google.genai.Client that replays recorded responses (no network, no API key).

Only the surface ControlPilot uses is implemented: ``client.models.generate_content(model=...,
contents=..., config=...)``. Each call pops the next recorded response from the script and
returns a real ``google.genai.types.GenerateContentResponse`` built from it, so your code sees the
same objects it would see from the live SDK. Every request is kept in ``client.models.requests``
so tests can inspect what you sent.

Note: the live SDK fills ``response.parsed`` when you pass ``response_schema``; this fake never
does. Parse ``response.text`` yourself and validate it: that is what you must do anyway, because
``parsed`` is silently ``None`` when the text does not validate.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from google.genai import types


class ScriptExhausted(AssertionError):
    """The code under test made more model calls than the recording contains."""


class FakeModels:
    def __init__(self, script: list[dict[str, Any]]):
        self._script = [copy.deepcopy(s) for s in script]
        self.requests: list[dict[str, Any]] = []

    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> types.GenerateContentResponse:
        self.requests.append({"model": model, "contents": copy.deepcopy(contents), "config": config})
        if not self._script:
            raise ScriptExhausted(f"no recorded response left for call #{len(self.requests)}")
        return types.GenerateContentResponse.model_validate(self._script.pop(0))

    @property
    def remaining(self) -> int:
        return len(self._script)


class FakeClient:
    def __init__(self, script: list[dict[str, Any]]):
        self.models = FakeModels(script)


def text_response(text: str, *, finish_reason: str = "STOP", prompt_tokens: int = 900, output_tokens: int = 120) -> dict:
    return {
        "candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finish_reason": finish_reason}],
        "usage_metadata": {"prompt_token_count": prompt_tokens, "candidates_token_count": output_tokens,
                           "total_token_count": prompt_tokens + output_tokens},
        "model_version": "gemini-3.8-flash",
    }


def call_response(name: str, args: dict, *, prompt_tokens: int = 850, output_tokens: int = 20) -> dict:
    return {
        "candidates": [{"content": {"role": "model", "parts": [{"function_call": {"name": name, "args": args}}]},
                        "finish_reason": "STOP"}],
        "usage_metadata": {"prompt_token_count": prompt_tokens, "candidates_token_count": output_tokens,
                           "total_token_count": prompt_tokens + output_tokens},
        "model_version": "gemini-3.8-flash",
    }


def load_script(path: str | Path) -> list[dict]:
    """A recorded script is a JSON list of raw GenerateContentResponse dicts."""
    return json.loads(Path(path).read_text())
