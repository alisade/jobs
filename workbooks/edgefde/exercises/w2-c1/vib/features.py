"""Time- and frequency-domain features and bearing-fault detection for one window.

TODO: implement every function below to the contract in README.md. Use numpy and
scipy.signal; the reference solution is about 120 lines.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def time_features(x: np.ndarray) -> dict[str, float]:
    """AC features of one window: {"rms", "peak", "crest_factor", "kurtosis"} (Pearson, Gaussian = 3)."""
    raise NotImplementedError("TODO")


def welch_psd(x: np.ndarray, fs: float, nperseg: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    """One-sided PSD (units^2/Hz) with a Hann window, 50% overlap, mean removed. Returns (f, pxx)."""
    raise NotImplementedError("TODO")


def frequency_resolution(fs: float, nperseg: int) -> float:
    raise NotImplementedError("TODO")


def band_energies(f: np.ndarray, pxx: np.ndarray, bands: list[tuple[float, float]]) -> list[float]:
    """Power in each [lo, hi) band: the PSD integrated over the band."""
    raise NotImplementedError("TODO")


def dominant_frequency(x: np.ndarray, fs: float, fmin: float = 1.0) -> float:
    """Strongest frequency above fmin, accurate to well under one FFT bin."""
    raise NotImplementedError("TODO")


def bearing_frequencies(shaft_hz: float, n_balls: int, ball_d: float, pitch_d: float,
                        contact_deg: float = 0.0) -> dict[str, float]:
    """{"bpfo", "bpfi", "bsf", "ftf"} in Hz from the shaft speed and bearing geometry."""
    raise NotImplementedError("TODO")


def envelope_spectrum(x: np.ndarray, fs: float, band: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    """Band-pass around the resonance, Hilbert envelope, mean removed, amplitude spectrum. Returns (f, mag)."""
    raise NotImplementedError("TODO")


@dataclass(frozen=True)
class FaultReport:
    bpfo_hz: float
    bpfi_hz: float
    bpfo_db: float
    bpfi_db: float
    fault: str | None  # "outer", "inner" or None


def detect_bearing_fault(x: np.ndarray, fs: float, shaft_hz: float, geometry: dict,
                         band: tuple[float, float] = (2_000.0, 4_500.0), tol: float = 0.03,
                         snr_db: float = 12.0) -> FaultReport:
    raise NotImplementedError("TODO")
