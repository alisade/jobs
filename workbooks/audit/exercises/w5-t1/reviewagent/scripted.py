"""A scripted stand-in for Gemini inside ADK (no network). Complete.

ScriptedLlm replays a list of recorded responses (dicts shaped like LlmResponse) in order and keeps
every LlmRequest it received in .requests. When the script runs out it answers with a short text,
so a run always terminates.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class ScriptedLlm(BaseLlm):
    model: str = "gemini-3.8-flash"
    script: list[dict[str, Any]] = []
    requests: list[Any] = []
    calls: int = 0

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        if self.calls < len(self.script):
            step = self.script[self.calls]
        else:
            step = {"content": {"role": "model", "parts": [{"text": '{"recommendation": "no_change", "reason": "script exhausted", "citations": []}'}]}}
        self.calls += 1
        yield LlmResponse(content=types.Content.model_validate(step["content"]),
                          usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=1200, candidates_token_count=60))


def scripted(script: list[dict[str, Any]]) -> ScriptedLlm:
    return ScriptedLlm(script=list(script), requests=[])
