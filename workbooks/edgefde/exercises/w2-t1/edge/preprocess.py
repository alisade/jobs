"""Gateway pre-processing: the accelerometer front end samples at 10 kHz; the analytics
pipeline runs at 2 kHz to save CPU and uplink bandwidth."""

from __future__ import annotations

import numpy as np

FS_RAW = 10_000
FS_OUT = 2_000


def downsample(x: np.ndarray, fs_in: int = FS_RAW, fs_out: int = FS_OUT) -> np.ndarray:
    """Reduce the sample rate from fs_in to fs_out (integer factor)."""
    if fs_in % fs_out:
        raise ValueError("integer factors only")
    factor = fs_in // fs_out
    return np.asarray(x, dtype=float)[::factor]
