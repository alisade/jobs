"""Deterministic stand-in for a text embedding model (text-embedding on Vertex AI in production).

Hashed bag of words with light stemming, L2-normalised: good enough to make chunking and metrics
matter, fully offline and reproducible. Do not change this file.
"""

from __future__ import annotations

import hashlib
import math
import re

DIM = 1024
STOP = set("a an the and or of to in on for is are was were be by with as at it its this that these those "
           "what which who how why when does do did can from into than then so not no".split())


def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP or len(w) < 2:
            continue
        for suf in ("ing", "es", "s"):
            if w.endswith(suf) and len(w) > len(suf) + 3:
                w = w[: -len(suf)]
                break
        out.append(w)
    return out


def embed(text: str) -> list[float]:
    v = [0.0] * DIM
    for t in tokens(text):
        h = int.from_bytes(hashlib.blake2b(t.encode(), digest_size=4).digest(), "big")
        v[h % DIM] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
