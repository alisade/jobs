"""Synthetic feature windows with named columns (do not edit)."""

from __future__ import annotations

import numpy as np

COLUMNS = ["rms", "peak", "crest", "kurtosis", "band1", "band2", "band3", "band4",
           "bpfo_db", "bpfi_db", "temp_c", "speed_rpm"]


def windows(n: int, fault_rate: float, seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < fault_rate).astype(int)
    X = rng.normal(0, 1, (n, len(COLUMNS)))
    sev = rng.uniform(0.3, 1.6, n) * y
    X[:, 0] += 0.8 * sev
    X[:, 3] += 1.4 * sev
    X[:, 6] += 1.1 * sev
    X[:, 8] += 1.8 * sev
    X[:, 9] *= 1.0 + 2.5 * sev
    X = X * np.array([0.3, 2.0, 0.5, 1.5, 0.1, 0.1, 0.2, 0.1, 4.0, 4.0, 6.0, 30.0]) + \
        np.array([1.0, 5.0, 3.0, 3.0, 0.5, 0.4, 0.3, 0.2, 0.0, 0.0, 45.0, 1770.0])
    t = {c: X[:, i].astype(np.float32) for i, c in enumerate(COLUMNS)}
    t["y"] = y
    return t


def to_v2_schema(t: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Feature store schema v2 (2026-10-28): kurtosis renamed to kurtosis_excess and made excess (minus 3)."""
    t = dict(t)
    t["kurtosis_excess"] = t.pop("kurtosis") - 3.0
    return t
