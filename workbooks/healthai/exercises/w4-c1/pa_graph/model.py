"""The recommendation model contract and a scripted chat model for offline tests.

In production the assess node calls Gemini on Agent Platform (Vertex AI). Here a scripted model
returns recorded responses per case id, so every test is deterministic and offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage
from pydantic import BaseModel, Field, field_validator


class CriterionResult(BaseModel):
    criterion_id: str
    met: bool
    citation: str = Field(min_length=1, description="policy section id that supports the finding")


class Recommendation(BaseModel):
    """What the model is allowed to say. It can recommend; it never decides."""

    outcome: Literal["approve", "deny", "pend"]
    confidence: float = Field(ge=0.0, le=1.0)
    criteria: list[CriterionResult] = Field(min_length=1)
    rationale: str = Field(min_length=10)

    @field_validator("rationale")
    @classmethod
    def no_empty_rationale(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("rationale must not be blank")
        return v


class ScriptedChatModel:
    """Stand-in for a chat model: returns the recorded content for the case id in the prompt.

    The prompt must contain a line "CASE: <case_id>". Calls are recorded in .calls for tests.
    """

    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[str] = []

    @classmethod
    def from_file(cls, path: str | Path) -> "ScriptedChatModel":
        return cls(json.loads(Path(path).read_text()))

    def invoke(self, messages: list[BaseMessage] | str) -> AIMessage:
        text = messages if isinstance(messages, str) else "\n".join(str(m.content) for m in messages)
        case_id = ""
        for line in text.splitlines():
            if line.startswith("CASE: "):
                case_id = line[6:].strip()
        self.calls.append(case_id)
        return AIMessage(content=self.responses.get(case_id, "I am not sure."))
