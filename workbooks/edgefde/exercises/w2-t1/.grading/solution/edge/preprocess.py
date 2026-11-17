"""Gateway pre-processing: the accelerometer front end samples at 10 kHz; the analytics
pipeline runs at 2 kHz to save CPU and uplink bandwidth.

Fixed: low-pass below the new Nyquist (1 kHz) BEFORE dropping samples. The MEMS sensor has no
analog anti-alias filter, so the 1298 Hz gear mesh is present in the 10 kHz stream; picking every
5th sample folds it to |1298 - 2000| = 702 Hz, inside the 600-900 Hz fault band.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

FS_RAW = 10_000
FS_OUT = 2_000


def downsample(x: np.ndarray, fs_in: int = FS_RAW, fs_out: int = FS_OUT) -> np.ndarray:
    """Reduce the sample rate from fs_in to fs_out (integer factor) with an anti-alias filter."""
    if fs_in % fs_out:
        raise ValueError("integer factors only")
    factor = fs_in // fs_out
    # polyphase FIR (Kaiser window): cutoff at the output Nyquist, > 80 dB stopband
    return signal.resample_poly(np.asarray(x, dtype=float), 1, factor)
