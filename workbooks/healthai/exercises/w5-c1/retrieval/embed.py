"""Offline stand-in for an embedding model (given; do not change).

Maps words to concepts from fixtures/concepts.json, so paraphrases land near each other the way a real
embedding model would put them. Codes, drug names and policy ids are out of vocabulary, as they often
are for real embeddings: that is the gap hybrid search closes.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from .text import tokenize

CONCEPTS: dict[str, str] = json.loads((Path(__file__).resolve().parent.parent / "fixtures" / "concepts.json").read_text())


def embed(text: str) -> dict[str, float]:
    """Sparse unit vector {concept: weight}. Empty dict if no known concept."""
    vec: dict[str, float] = {}
    for tok in tokenize(text):
        c = CONCEPTS.get(tok)
        if c:
            vec[c] = vec.get(c, 0.0) + 1.0
    norm = math.sqrt(sum(v * v for v in vec.values()))
    return {k: v / norm for k, v in vec.items()} if norm else {}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(v * b.get(k, 0.0) for k, v in a.items())
