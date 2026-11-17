"""Tokenizer shared by BM25, the embedding stub and the reranker stub (given)."""

from __future__ import annotations

import re

TOKEN = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
STOP = {"a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "with", "policy", "is", "be"}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]
