"""Replays the recorded Gemini responses for the Q3 CM-03 run (no network, no API key). Do not edit.

The recordings were captured from the same model twice: once with constrained decoding (the
request carried a response_schema) and once without (JSON mode only). The fake picks the
recording that matches what your request asks for, the way the live model would behave:

- config.response_schema set     -> fixtures/recorded/constrained.json (keys follow the schema)
- only response_mime_type=json    -> fixtures/recorded/freeform.json   (keys follow the prompt text)

The sample is identified by the change id in the request contents.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from google.genai import types

REC = Path(__file__).resolve().parents[1] / "fixtures" / "recorded"


def _flatten(contents: Any) -> str:
    if isinstance(contents, str):
        return contents
    if isinstance(contents, list):
        return " ".join(_flatten(c) for c in contents)
    if isinstance(contents, types.Content):
        return " ".join(p.text or "" for p in (contents.parts or []))
    return str(contents)


class FakeModels:
    def __init__(self) -> None:
        self.constrained = json.loads((REC / "constrained.json").read_text())
        self.freeform = json.loads((REC / "freeform.json").read_text())
        self.requests: list[dict] = []

    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> types.GenerateContentResponse:
        self.requests.append({"model": model, "contents": contents, "config": config})
        m = re.search(r"CHG-\d{6}", _flatten(contents))
        if not m:
            raise AssertionError("request contents do not name a change id")
        cid = m.group(0)
        schema = getattr(config, "response_schema", None) or getattr(config, "response_json_schema", None)
        text = (self.constrained if schema is not None else self.freeform)[cid]
        return types.GenerateContentResponse.model_validate({
            "candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finish_reason": "STOP"}],
            "usage_metadata": {"prompt_token_count": 1450, "candidates_token_count": 140, "total_token_count": 1590},
            "model_version": "gemini-3.8-flash",
        })


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()
