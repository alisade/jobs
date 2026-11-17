"""Synthetic continuous accelerometer stream (do not edit).

The sensor is a DC-coupled MEMS accelerometer mounted vertically, so every sample carries about
+1 g of gravity, plus shaft vibration at 29.5 Hz and broadband noise. A bearing defect adds
impacts ringing a 3.2 kHz resonance.
"""

from __future__ import annotations

import numpy as np

FS = 20_000


def stream(seconds: float = 30.0, seed: int = 0, fault_hz: float | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(FS * seconds)
    t = np.arange(n) / FS
    x = 1.0 + 0.3 * np.sin(2 * np.pi * 29.5 * t) + rng.normal(0, 0.05, n)
    if fault_hz:
        rt = np.arange(int(0.004 * FS)) / FS
        ring = np.exp(-rt * 900) * np.sin(2 * np.pi * 3200 * rt)
        imp = np.zeros(n)
        imp[(np.arange(0, seconds, 1 / fault_hz) * FS).astype(int)] = 1.5
        x += np.convolve(imp, ring)[:n]
    return x


def chunks(x: np.ndarray, size: int = FS):
    for i in range(0, len(x), size):
        yield x[i:i + size]
