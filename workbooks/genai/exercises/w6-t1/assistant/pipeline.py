"""Request path: cache first, then the agent."""

from __future__ import annotations

from dataclasses import dataclass

from .backend import FakeAgent
from .cache import AnswerCache


@dataclass
class Answer:
    text: str
    cache_hit: bool


@dataclass
class Assistant:
    agent: FakeAgent
    cache: AnswerCache

    def ask(self, user_id: str, store_id: str, question: str) -> Answer:
        cached = self.cache.get(question, user_id, store_id)
        if cached is not None:
            return Answer(cached, True)
        r = self.agent.run(user_id, store_id, question)
        self.cache.put(question, user_id, store_id, r.text, r.tools_used)
        return Answer(r.text, False)
