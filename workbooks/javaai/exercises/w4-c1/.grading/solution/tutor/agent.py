"""The tutor agent loop with guardrails (what ADK callbacks and tool filters do, written out)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from . import tools
from .model import FinalText, ToolCall, TutorModel

MAX_TOOL_CALLS = 4
FALLBACK = "I could not finish that one. Can you ask about a smaller part of the lesson?"
REFUSAL = "I can help with this course's material. Ask me about a topic from your lessons."
WITHHELD = ("I can't give you the quiz answer, but here is a hint: re-read the section you are working on "
            "and tell me which idea you think the question is testing.")


@dataclass
class TurnResult:
    reply: str
    tool_calls: list[str] = field(default_factory=list)
    refused: bool = False
    withheld: bool = False


class SearchArgs(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    k: int = Field(default=2, ge=1, le=5)


class ProgressArgs(BaseModel):
    pass


# allow-list: name -> (args model, runner bound to the session). Write tools are simply not here.
def _search(session: dict, a: SearchArgs) -> Any:
    return tools.search_course(session["course_id"], a.query, a.k)


def _progress(session: dict, a: ProgressArgs) -> Any:
    return tools.get_learner_progress(session["learner_id"], session["course_id"])


ALLOWED = {"search_course": (SearchArgs, _search), "get_learner_progress": (ProgressArgs, _progress)}


def on_topic(message: str, course_id: str) -> bool:
    words = set(re.findall(r"[a-z0-9]+", message.lower()))
    for kw in tools.course_keywords(course_id):
        if any(w.startswith(kw) or kw.startswith(w) and len(w) >= 4 for w in words):
            return True
    return False


class TutorAgent:
    def __init__(self, model: TutorModel):
        self.model = model

    def run_turn(self, learner_id: str, course_id: str, message: str) -> TurnResult:
        # before-model guard: off-topic requests never reach the model
        if not on_topic(message, course_id):
            return TurnResult(reply=REFUSAL, refused=True)
        session = {"learner_id": learner_id, "course_id": course_id}
        history: list[dict] = [{"role": "user", "text": message}]
        names = list(ALLOWED)
        called: list[str] = []
        for _ in range(MAX_TOOL_CALLS + 1):
            turn = self.model.next_turn(history, names)
            if isinstance(turn, FinalText):
                return self._after_model(turn.text, learner_id, course_id, called)
            if len(called) >= MAX_TOOL_CALLS:
                break
            called.append(turn.name)
            history.append({"role": "tool", "name": turn.name, "result": self._dispatch(session, turn)})
        return TurnResult(reply=FALLBACK, tool_calls=called)

    @staticmethod
    def _dispatch(session: dict, call: ToolCall) -> Any:
        entry = ALLOWED.get(call.name)
        if entry is None:
            return {"error": f"tool '{call.name}' is not available. Available: {sorted(ALLOWED)}"}
        model_cls, run = entry
        args = {k: v for k, v in (call.args or {}).items() if k not in ("learner_id", "course_id")}
        try:
            parsed = model_cls.model_validate(args)
        except ValidationError as e:
            return {"error": "invalid arguments: " + "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())}
        try:
            return run(session, parsed)
        except Exception as e:  # tool failures go back to the model, not to the learner as a 500
            return {"error": f"{call.name} failed: {type(e).__name__}"}

    @staticmethod
    def _after_model(text: str, learner_id: str, course_id: str, called: list[str]) -> TurnResult:
        answer = tools.current_quiz_answer(learner_id, course_id)
        if answer and answer.lower() in text.lower():
            return TurnResult(reply=WITHHELD, tool_calls=called, withheld=True)
        return TurnResult(reply=text, tool_calls=called)
