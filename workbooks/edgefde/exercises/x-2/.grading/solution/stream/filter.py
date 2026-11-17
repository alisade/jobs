"""Band-pass for the live accelerometer stream (500 Hz - 4 kHz, 4th-order Butterworth).

Fixed: the filter keeps its internal state (zi) between chunks, so chunk boundaries are invisible
and the output equals filtering the whole stream in one go. On the first chunk the state is
initialised to the steady state for the first sample (sosfilt_zi * x[0]), so the +1 g gravity offset
does not produce a start-up step either.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

FS = 20_000
BAND = (500.0, 4_000.0)


class StreamingBandpass:
    def __init__(self, fs: float = FS, band: tuple[float, float] = BAND, order: int = 4) -> None:
        self.sos = signal.butter(order, band, btype="bandpass", fs=fs, output="sos")
        self.zi: np.ndarray | None = None

    def process(self, chunk: np.ndarray) -> np.ndarray:
        x = np.asarray(chunk, dtype=float)
        if x.size == 0:
            return x
        if self.zi is None:
            self.zi = signal.sosfilt_zi(self.sos) * x[0]
        y, self.zi = signal.sosfilt(self.sos, x, zi=self.zi)
        return y

    def reset(self) -> None:
        self.zi = None
