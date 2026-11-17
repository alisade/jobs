"""A deterministic stand-in for Gemini inside ADK (no network). Do not edit.

It behaves like a well-instructed model: ask for the next batch, test every change in it with
parallel tool calls, then stop. It decides only from the tool results it has seen in this
invocation, the way the real model only sees what is in its context.
"""

from __future__ import annotations

from typing import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class PolicyLlm(BaseLlm):
    model: str = "policy-gemini"

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        last = None
        for c in reversed(llm_request.contents or []):
            frs = [p.function_response for p in (c.parts or []) if p.function_response]
            if frs:
                last = frs
                break
            if c.role == "user" and any(p.text for p in (c.parts or [])):
                break
        if last is None:
            parts = [types.Part(function_call=types.FunctionCall(name="next_batch", args={}))]
        elif last[0].name == "next_batch":
            ids = (last[0].response or {}).get("change_ids", [])
            if not ids:
                parts = [types.Part(text="Nothing left to test in this sample.")]
            else:
                parts = [types.Part(function_call=types.FunctionCall(name="test_change", args={"change_id": i})) for i in ids]
        else:
            parts = [types.Part(text=f"Batch complete: {len(last)} change(s) tested.")]
        yield LlmResponse(content=types.Content(role="model", parts=parts))
