"""A scripted stand-in for Gemini inside ADK (no network). Complete; do not edit.

ADK lets you plug in any model by subclassing BaseLlm. ScriptedLlm returns the next Content from
its script on every model call, so a test can make "the model" request any tool with any argument.
Every LlmRequest is kept in `requests`.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class ScriptedLlm(BaseLlm):
    model: str = "scripted-gemini"
    script: list[Any] = []
    requests: list[Any] = []
    n: int = 0

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        if self.n >= len(self.script):
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text='{"error": "script exhausted"}')]))
            return
        step = self.script[self.n]
        self.n += 1
        yield LlmResponse(content=step)


def call(name: str, **args) -> types.Content:
    return types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])


def calls(*pairs: tuple[str, dict]) -> types.Content:
    return types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=n, args=a)) for n, a in pairs])


def say(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])
