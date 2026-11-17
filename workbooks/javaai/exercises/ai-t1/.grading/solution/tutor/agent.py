"""The tutor agent (ADK LlmAgent shape): instruction, tools from an McpToolset, and the run loop."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .model import Final, ToolCall
from .toolset import McpToolset

# Enforced in code, whatever the toolset or the instruction says: the tutor only ever reads.
READ_ONLY_TOOLS = frozenset({"list_lessons", "get_lesson"})
CONFIG = Path(__file__).resolve().parent.parent / "config" / "agent.yaml"


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text())


def sanitize(result):
    """Course text is untrusted data: drop hidden markup and label it before the model sees it."""
    if isinstance(result, dict) and isinstance(result.get("text"), str):
        text = re.sub(r"(?s)<[^>]*display\s*:\s*none[^>]*>.*?</[^>]+>", "", result["text"])
        text = re.sub(r"<[^>]+>", "", text)
        return {**result, "text": " ".join(text.split()), "content_trust": "untrusted"}
    return result


class TutorAgent:
    def __init__(self, model, config: dict | None = None):
        self.config = config or load_config()
        self.model = model
        self.toolset = McpToolset(tool_filter=self.config["mcp"].get("tool_filter"))
        self.tools = {k: v for k, v in self.toolset.get_tools().items() if k in READ_ONLY_TOOLS}

    def run(self, learner_id: str, message: str, max_steps: int = 6) -> dict:
        history: list[dict] = [{"role": "user", "text": message}]
        calls: list[str] = []
        for _ in range(max_steps):
            turn = self.model.next_turn(self.config["instruction"], history, sorted(self.tools))
            if isinstance(turn, Final):
                return {"reply": turn.text, "tool_calls": calls}
            assert isinstance(turn, ToolCall)
            calls.append(turn.name)
            args = dict(turn.args)
            if "learner_id" in args:
                args["learner_id"] = learner_id
            fn = self.tools.get(turn.name)
            if fn is None:
                result = {"error": f"tool '{turn.name}' is not available to the tutor"}
            else:
                result = sanitize(fn(**args))
            history.append({"role": "tool", "name": turn.name, "args": turn.args, "result": result})
        return {"reply": "Let's take a step back. What part of the lesson is unclear?", "tool_calls": calls}
