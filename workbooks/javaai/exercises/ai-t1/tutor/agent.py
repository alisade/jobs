"""The tutor agent (ADK LlmAgent shape): instruction, tools from an McpToolset, and the run loop."""

from __future__ import annotations

from pathlib import Path

import yaml

from . import backend
from .model import Final, ToolCall
from .toolset import McpToolset

CONFIG = Path(__file__).resolve().parent.parent / "config" / "agent.yaml"


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text())


class TutorAgent:
    def __init__(self, model, config: dict | None = None):
        self.config = config or load_config()
        self.model = model
        self.toolset = McpToolset(tool_filter=self.config["mcp"].get("tool_filter"))
        self.tools = self.toolset.get_tools()

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
            fn = self.tools.get(turn.name) or backend.SERVER_TOOLS[turn.name]
            history.append({"role": "tool", "name": turn.name, "args": turn.args, "result": fn(**args)})
        return {"reply": "Let's take a step back. What part of the lesson is unclear?", "tool_calls": calls}
