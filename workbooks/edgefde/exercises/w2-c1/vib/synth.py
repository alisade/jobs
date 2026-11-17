"""Synthetic accelerometer signals with known content (complete: do not edit).

A rolling-element bearing defect produces a short impact every time a ball passes it.
Each impact rings the housing's structural resonance (a few kHz) and decays, so the
fault shows up as a train of decaying bursts repeating at the defect frequency, i.e.
amplitude modulation of the resonance. The spectrum of the raw signal shows energy
around the resonance; the envelope spectrum shows the repetition rate (BPFO, BPFI).
"""

from __future__ import annotations

import numpy as np


def tones(fs: float, seconds: float, freqs_amps: list[tuple[float, float]], noise: float = 0.0,
          dc: float = 0.0, seed: int = 0) -> np.ndarray:
    n = int(round(fs * seconds))
    t = np.arange(n) / fs
    x = np.full(n, dc, dtype=float)
    for f, a in freqs_amps:
        x += a * np.sin(2 * np.pi * f * t)
    if noise:
        x += np.random.default_rng(seed).normal(0, noise, n)
    return x


def bearing_signal(fs: float = 20_000.0, seconds: float = 2.0, shaft_hz: float = 29.5,
                   fault_hz: float | None = None, fault_amp: float = 1.0, resonance_hz: float = 3_200.0,
                   noise: float = 0.3, seed: int = 0, modulate_by_shaft: bool = False) -> np.ndarray:
    """Shaft tone + 2x harmonic + broadband noise, plus an optional impact train at fault_hz."""
    rng = np.random.default_rng(seed)
    n = int(round(fs * seconds))
    t = np.arange(n) / fs
    x = 0.4 * np.sin(2 * np.pi * shaft_hz * t) + 0.15 * np.sin(2 * np.pi * 2 * shaft_hz * t)
    x += rng.normal(0, noise, n)
    if fault_hz:
        ring_t = np.arange(int(0.004 * fs)) / fs
        ring = np.exp(-ring_t * 900.0) * np.sin(2 * np.pi * resonance_hz * ring_t)
        impacts = np.zeros(n)
        k = 0.0
        while k < seconds:
            i = int(k * fs + rng.normal(0, 0.0004 * fs))  # small slip jitter, as in real bearings
            if 0 <= i < n:
                gain = 1.0
                if modulate_by_shaft:  # inner race: load zone modulation at shaft speed
                    gain = 0.6 + 0.4 * np.cos(2 * np.pi * shaft_hz * k)
                impacts[i] += fault_amp * gain
            k += 1.0 / fault_hz
        x += np.convolve(impacts, ring)[:n]
    return x
