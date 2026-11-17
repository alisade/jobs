"""Lexical retrieval over chunks (given). The production pipeline adds dense vectors; the regression
reproduces with this BM25-only path, which has no embedding model at all."""

from __future__ import annotations

import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9]+")


def tok(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        self.tf = [Counter(tok(t)) for t in texts]
        self.dl = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.dl) / max(len(self.dl), 1)
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(texts)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def top(self, query: str, k: int) -> list[int]:
        scores = []
        for i, c in enumerate(self.tf):
            s = 0.0
            for t in tok(query):
                f = c.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avg))
            scores.append((s, -i))
        return [-i for s, i in sorted(scores, reverse=True)[:k]]
