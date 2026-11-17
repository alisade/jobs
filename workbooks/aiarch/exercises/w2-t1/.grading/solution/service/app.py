"""Access-review assistant: one request = one turn of a manager's chat session.

The Runtime calls HelpdeskService.handle(session_id, user, team, text) per request. A session is
one manager's conversation (runtimeSessionId); the specialist remembers earlier turns of the SAME
session and nothing from any other session.

Fix (INC-20433): the specialist used to be a module-level singleton, so every session in the
process shared one Agent and its message history. Agents are now owned by a per-session registry
with an LRU bound and an idle timeout, so state is isolated and memory stays bounded.
"""
from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Callable

from strands import Agent, tool
from strands.models.model import Model

from . import config

DATA = __import__("pathlib").Path(__file__).resolve().parent.parent / "data"


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
        self._sessions: OrderedDict[str, tuple[Agent, float, str]] = OrderedDict()
        self._lock = threading.Lock()
        self._busy: dict[str, threading.Lock] = {}

    def _evict(self, now: float) -> None:
        for sid in [s for s, (_, last, _) in self._sessions.items() if now - last > self.idle_seconds]:
            del self._sessions[sid]
            self._busy.pop(sid, None)
        while len(self._sessions) > self.max_sessions:
            sid, _ = self._sessions.popitem(last=False)
            self._busy.pop(sid, None)

    def _specialist(self, session_id: str, team: str) -> tuple[Agent, threading.Lock]:
        with self._lock:
            now = self.clock()
            self._evict(now)
            entry = self._sessions.get(session_id)
            if entry is None or entry[2] != team:
                agent = Agent(name="access_reviews", model=self.model_factory("access_reviews", session_id),
                              system_prompt=config.SYSTEM_PROMPT, tools=_review_tools(team), callback_handler=None)
            else:
                agent = entry[0]
            self._sessions[session_id] = (agent, now, team)
            self._sessions.move_to_end(session_id)
            self._evict(now)
            busy = self._busy.setdefault(session_id, threading.Lock())
            return agent, busy

    def active_sessions(self) -> int:
        with self._lock:
            return len(self._sessions)

    def handle(self, session_id: str, user: str, team: str, text: str) -> str:
        agent, busy = self._specialist(session_id, team)
        with busy:  # one turn at a time per session; different sessions run in parallel
            return str(agent(f"[{user}] {text}")).strip()
