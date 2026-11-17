"""Helpers shared by the visible tests: fixture paths and a small transcript builder for
hand-crafted cases."""

from __future__ import annotations

from pathlib import Path

from evals.transcript import Transcript, load_transcript

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
TRANSCRIPTS = FIXTURES / "transcripts"
VERDICTS = FIXTURES / "judge_verdicts.json"


def fixture(scenario: str, run: int) -> Transcript:
    return load_transcript(TRANSCRIPTS / f"{scenario}--run{run}.json")


class T:
    """Build a transcript block by block: T().user("hi").call("search_products", {...})
    .result("...").text("...").build()."""

    def __init__(self, scenario: str = "crafted", run: int = 1) -> None:
        self.scenario, self.run = scenario, run
        self.messages: list[dict] = []
        self._n = 0
        self._last_id = ""

    def user(self, text: str) -> T:
        self.messages.append({"role": "user", "content": text})
        return self

    def _assistant_blocks(self) -> list[dict]:
        if not self.messages or self.messages[-1]["role"] != "assistant":
            self.messages.append({"role": "assistant", "content": []})
        return self.messages[-1]["content"]

    def text(self, text: str) -> T:
        self._assistant_blocks().append({"type": "text", "text": text})
        return self

    def call(self, name: str, inp: dict | None = None) -> T:
        self._n += 1
        self._last_id = f"toolu_{self._n:03d}"
        self._assistant_blocks().append({"type": "tool_use", "id": self._last_id, "name": name, "input": inp or {}})
        return self

    def result(self, content, is_error: bool = False, tool_use_id: str | None = None) -> T:
        block = {"type": "tool_result", "tool_use_id": tool_use_id or self._last_id, "content": content}
        if is_error:
            block["is_error"] = True
        if self.messages and self.messages[-1]["role"] == "user" and isinstance(self.messages[-1]["content"], list):
            self.messages[-1]["content"].append(block)
        else:
            self.messages.append({"role": "user", "content": [block]})
        return self

    def build(self) -> Transcript:
        return Transcript(self.scenario, self.run, self.messages)
