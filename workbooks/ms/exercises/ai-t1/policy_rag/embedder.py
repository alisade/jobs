"""Deterministic hashing bag-of-words embedders, versioned like a real embedding model.

Same dimensions for every version, on purpose: like swapping text-embedding models of equal
size, a mismatch does NOT raise a dimension error. It just produces meaningless similarities.
"""
from __future__ import annotations

import hashlib
import math
import re

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from", "how", "i",
    "if", "in", "is", "it", "many", "much", "my", "of", "on", "or", "the", "to", "what", "when",
    "with", "you", "your", "per",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _stem(tok: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(tok) > 4 and tok.endswith(suffix):
            return tok[: -len(suffix)]
    return tok


def tokens_v1(text: str) -> list[str]:
    return [t for t in _words(text) if t not in STOPWORDS]


def tokens_v2(text: str) -> list[str]:
    toks = [_stem(t) for t in _words(text) if t not in STOPWORDS]
    return toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]


class HashBowEmbedder:
    def __init__(self, name: str, salt: str, tokenizer, dims: int = 1024):
        self.name = name
        self.salt = salt
        self.tokenizer = tokenizer
        self.dims = dims

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dims
        for tok in self.tokenizer(text):
            h = int(hashlib.md5((self.salt + tok).encode()).hexdigest(), 16)
            vec[h % self.dims] += 1.0 if (h >> 64) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


EMBEDDERS = {
    "hash-bow-v1": HashBowEmbedder("hash-bow-v1", "litware-v1:", tokens_v1),
    "hash-bow-v2": HashBowEmbedder("hash-bow-v2", "litware-v2:", tokens_v2),
}


def get_embedder(name: str) -> HashBowEmbedder:
    try:
        return EMBEDDERS[name]
    except KeyError:
        raise KeyError(f"unknown embedder {name!r}; known: {sorted(EMBEDDERS)}") from None
