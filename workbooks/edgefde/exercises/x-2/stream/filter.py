"""Band-pass for the live accelerometer stream (500 Hz - 4 kHz, 4th-order Butterworth).

The gateway receives the stream in 1-second chunks from the sensor driver and filters each chunk
before computing alert features.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

FS = 20_000
BAND = (500.0, 4_000.0)


class StreamingBandpass:
    def __init__(self, fs: float = FS, band: tuple[float, float] = BAND, order: int = 4) -> None:
        self.sos = signal.butter(order, band, btype="bandpass", fs=fs, output="sos")

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Filter one chunk of the continuous stream."""
        return signal.sosfilt(self.sos, np.asarray(chunk, dtype=float))

    def reset(self) -> None:
        """Forget the stream history (call after a sensor reconnect)."""
