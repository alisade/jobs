"""Per-chunk impact alerting on the band-passed stream (do not edit)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

KURTOSIS_LIMIT = 6.0
CREST_LIMIT = 7.0


@dataclass(frozen=True)
class ChunkAlert:
    index: int
    kurtosis: float
    crest: float
    alert: bool


def score(index: int, y: np.ndarray) -> ChunkAlert:
    yc = y - y.mean()
    m2 = float(np.mean(yc ** 2)) or 1e-30
    k = float(np.mean(yc ** 4) / m2 ** 2)
    crest = float(np.max(np.abs(yc)) / np.sqrt(m2))
    return ChunkAlert(index, k, crest, k > KURTOSIS_LIMIT or crest > CREST_LIMIT)
