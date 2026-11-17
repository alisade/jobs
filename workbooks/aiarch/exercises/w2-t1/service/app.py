"""Access-review assistant: one request = one turn of a manager's chat session.

The Runtime calls HelpdeskService.handle(session_id, user, team, text) per request. A session is
one manager's conversation (runtimeSessionId); the specialist should remember earlier turns of
the SAME session ("and the second one?") and nothing from any other session.
"""
from __future__ import annotations

import json
import time
from typing import Callable

from strands import Agent, tool
from strands.models.model import Model

from . import config

DATA = __import__("pathlib").Path(__file__).resolve().parent.parent / "data"

_SPECIALIST: Agent | None = None   # created on first use: avoids paying agent setup per request


def _review_tools(team: str) -> list:
    reviews = json.loads((DATA / "reviews.json").read_text())

    @tool
    def list_pending_reviews() -> dict:
        """List pending access reviews for the signed-in manager's team."""
        items = [r for r in reviews if r["team"] == team and r["status"] == "pending"]
        return {"team": team, "reviews": [{k: r[k] for k in ("id", "user", "entitlement")} for r in items]}

    return [list_pending_reviews]


class HelpdeskService:
    def __init__(self, model_factory: Callable[[str, str], Model], max_sessions: int = 500,
                 idle_seconds: float = 1800, clock: Callable[[], float] = time.monotonic):
        self.model_factory = model_factory
        self.max_sessions = max_sessions
        self.idle_seconds = idle_seconds
        self.clock = clock

    def _specialist(self, session_id: str, team: str) -> Agent:
        global _SPECIALIST
        if _SPECIALIST is None:
            _SPECIALIST = Agent(name="access_reviews", model=self.model_factory("access_reviews", session_id),
                                system_prompt=config.SYSTEM_PROMPT, tools=_review_tools(team), callback_handler=None)
        return _SPECIALIST

    def active_sessions(self) -> int:
        return 1 if _SPECIALIST is not None else 0

    def handle(self, session_id: str, user: str, team: str, text: str) -> str:
        agent = self._specialist(session_id, team)
        return str(agent(f"[{user}] {text}")).strip()
