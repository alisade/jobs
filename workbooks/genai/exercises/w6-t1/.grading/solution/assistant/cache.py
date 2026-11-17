"""Answer cache in front of the assistant. Reference solution: cache by data class.

  static    policy/FAQ answers (no tools, or policy_lookup only)   global key, 24 h
  catalog   product facts from search_products (prices, names)     global key, 1 h
  volatile  anything that read check_inventory                     key scoped to the store, 60 s
  personal  anything that read customer data (get_order_status)    never cached

An answer's class is the most sensitive class of any tool it used.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable

TTL_S = 24 * 3600
TTL_BY_CLASS = {"static": 24 * 3600, "catalog": 3600, "volatile": 60}
PERSONAL_TOOLS = {"get_order_status"}
VOLATILE_TOOLS = {"check_inventory"}
CATALOG_TOOLS = {"search_products"}


def normalize(question: str) -> str:
    q = re.sub(r"[^a-z0-9 ]+", " ", question.lower())
    return " ".join(q.split())


def classify(tools_used: list[str]) -> str:
    used = set(tools_used)
    if used & PERSONAL_TOOLS:
        return "personal"
    if used & VOLATILE_TOOLS:
        return "volatile"
    if used & CATALOG_TOOLS:
        return "catalog"
    return "static"


@dataclass
class Entry:
    text: str
    expires_at: float
    tools_used: list[str]
    data_class: str = "static"


@dataclass
class AnswerCache:
    clock: Callable[[], float] = time.time
    entries: dict[str, Entry] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def key(self, question: str, user_id: str, store_id: str, data_class: str = "static") -> str:
        base = normalize(question)
        if data_class == "volatile":
            return f"{base}|store={store_id}"
        return base

    def get(self, question: str, user_id: str, store_id: str) -> str | None:
        now = self.clock()
        for k in (self.key(question, user_id, store_id), self.key(question, user_id, store_id, "volatile")):
            e = self.entries.get(k)
            if e and e.expires_at > now:
                self.hits += 1
                return e.text
        self.misses += 1
        return None

    def put(self, question: str, user_id: str, store_id: str, text: str, tools_used: list[str]) -> None:
        data_class = classify(tools_used)
        if data_class == "personal":
            return
        k = self.key(question, user_id, store_id, data_class)
        self.entries[k] = Entry(text=text, expires_at=self.clock() + TTL_BY_CLASS[data_class],
                                tools_used=list(tools_used), data_class=data_class)
