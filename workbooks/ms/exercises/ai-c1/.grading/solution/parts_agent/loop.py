"""The agent loop. Reference solution."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from parts_agent.session import SYSTEM_PROMPT, Session
from parts_agent.tools import TOOLS, execute_tool

TURN_LIMIT_TEXT = "I could not finish this request within the step limit. Please try again or call the parts desk."


@dataclass
class RunResult:
    final_text: str
    stop_reason: str                      # end_turn | max_tokens | max_turns
    model_calls: int
    tool_calls: list[dict] = field(default_factory=list)   # {"name", "input", "is_error"}
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})


def _result_block(tool_use_id: str, body: dict, is_error: bool) -> dict:
    return {"type": "tool_result", "tool_use_id": tool_use_id,
            "content": json.dumps(body, sort_keys=True), "is_error": is_error}


def _texts(content: list[dict]) -> str:
    return "\n".join(b.get("text", "") for b in content if b.get("type") == "text").strip()


def run_turn(client, session: Session, user_text: str, *, max_turns: int = 8,
             model: str = "fake-model", max_tokens: int = 1024) -> RunResult:
    session.messages.append({"role": "user", "content": user_text})
    result = RunResult(final_text="", stop_reason="", model_calls=0)

    while True:
        if result.model_calls >= max_turns:
            result.stop_reason = "max_turns"
            result.final_text = TURN_LIMIT_TEXT
            return result
        resp = client.create(model=model, system=SYSTEM_PROMPT, messages=session.messages,
                             tools=TOOLS, max_tokens=max_tokens)
        result.model_calls += 1
        usage = resp.get("usage") or {}
        result.usage["input_tokens"] += int(usage.get("input_tokens", 0) or 0)
        result.usage["output_tokens"] += int(usage.get("output_tokens", 0) or 0)
        content = resp.get("content") or []
        session.messages.append({"role": "assistant", "content": content})
        uses = [b for b in content if b.get("type") == "tool_use"]
        stop = resp.get("stop_reason")

        if stop == "tool_use" and uses:
            if result.model_calls >= max_turns:
                # Do not execute: answer every tool_use so the history stays valid, then stop.
                session.messages.append({"role": "user", "content": [
                    _result_block(u["id"], {"error": "turn_limit", "message": "step limit reached; not executed"}, True)
                    for u in uses]})
                result.stop_reason = "max_turns"
                result.final_text = TURN_LIMIT_TEXT
                return result
            blocks = []
            for u in uses:  # execute in the order the model emitted them
                body, is_error = execute_tool(session, u.get("name"), u.get("input"))
                result.tool_calls.append({"name": u.get("name"), "input": u.get("input"), "is_error": is_error})
                blocks.append(_result_block(u["id"], body, is_error))
            session.messages.append({"role": "user", "content": blocks})
            continue

        if stop == "max_tokens":
            if uses:
                session.messages.append({"role": "user", "content": [
                    _result_block(u["id"], {"error": "truncated", "message": "response was cut off; not executed"}, True)
                    for u in uses]})
            result.stop_reason = "max_tokens"
            result.final_text = _texts(content)
            return result

        result.stop_reason = "end_turn"
        result.final_text = _texts(content)
        return result
