"""A recorded judge: replays verdicts captured from a real grading model. Given.

Like an HTTP cassette, a recording is keyed by the request: here the sha256 of the judge
prompt (``judge_key``). A prompt that differs by one byte from the one recorded has no
verdict, which is exactly how a non-deterministic prompt shows up in CI. The fake also
refuses ``temperature != 0``: the recordings were made at 0.

The interface is the slice of ``anthropic.Anthropic().messages.create`` a judge uses, so
the same ``judge_check`` code runs against the real client in ``make live``-style runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def judge_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


class MissingRecording(KeyError):
    """No recorded verdict for this exact prompt."""


class _Messages:
    def __init__(self, recordings: dict[str, str]) -> None:
        self._recordings = recordings
        self.calls: list[dict[str, Any]] = []

    def create(self, *, model: str, max_tokens: int, messages: list[dict[str, Any]], **kw: Any):
        self.calls.append({"model": model, "max_tokens": max_tokens, "messages": messages, **kw})
        if kw.get("temperature") != 0:
            raise ValueError("recorded judge verdicts were made at temperature=0; pass temperature=0")
        if len(messages) != 1 or messages[0].get("role") != "user":
            raise ValueError("the judge takes exactly one user message")
        content = messages[0]["content"]
        if not isinstance(content, str):
            raise ValueError("pass the judge prompt as a plain string")
        key = judge_key(content)
        if key not in self._recordings:
            raise MissingRecording(key)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self._recordings[key])],
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=len(content) // 4, output_tokens=40),
        )


class FakeJudgeClient:
    def __init__(self, recordings: dict[str, str]) -> None:
        self.messages = _Messages(recordings)

    @classmethod
    def from_file(cls, path: Path) -> FakeJudgeClient:
        return cls(json.loads(Path(path).read_text()))
