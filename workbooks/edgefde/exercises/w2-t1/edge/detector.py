"""Outer-race early warning on the 2 kHz stream (do not edit: tuned and signed off by reliability).

The Dunmore pumps' outer-race defect excites a housing mode at 740-800 Hz. The detector flags a
capture when the strongest line in the 600-900 Hz band is more than THRESHOLD_DB above the median
of the whole spectrum.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BAND = (600.0, 900.0)
THRESHOLD_DB = 25.0


@dataclass(frozen=True)
class Verdict:
    flagged: bool
    peak_hz: float
    peak_db: float


def detect(x: np.ndarray, fs: float) -> Verdict:
    x = np.asarray(x, dtype=float)
    w = np.hanning(len(x))
    mag = np.abs(np.fft.rfft((x - x.mean()) * w))
    f = np.fft.rfftfreq(len(x), 1 / fs)
    m = (f >= BAND[0]) & (f <= BAND[1])
    k = np.flatnonzero(m)[np.argmax(mag[m])]
    db = 20 * np.log10(mag[k] / (np.median(mag[1:]) + 1e-30))
    return Verdict(bool(db > THRESHOLD_DB), float(f[k]), float(db))
