"""Time- and frequency-domain features and bearing-fault detection for one window."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import signal


def _check(x: np.ndarray, fs: float | None = None, min_len: int = 64) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.ndim != 1:
        raise ValueError("expected a 1-D signal")
    if len(x) < min_len:
        raise ValueError(f"window too short: {len(x)} samples, need >= {min_len}")
    if not np.all(np.isfinite(x)):
        raise ValueError("signal contains NaN or infinity")
    if fs is not None and not (fs > 0 and math.isfinite(fs)):
        raise ValueError("fs must be a positive number")
    return x


def time_features(x: np.ndarray) -> dict[str, float]:
    x = _check(x)
    xc = x - x.mean()  # AC features: a DC offset (sensor bias) is not vibration
    rms = float(np.sqrt(np.mean(xc ** 2)))
    peak = float(np.max(np.abs(xc)))
    m2 = np.mean(xc ** 2)
    kurt = float(np.mean(xc ** 4) / m2 ** 2) if m2 > 0 else 0.0
    return {"rms": rms, "peak": peak, "crest_factor": peak / rms if rms > 0 else 0.0, "kurtosis": kurt}


def welch_psd(x: np.ndarray, fs: float, nperseg: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    x = _check(x, fs)
    nperseg = min(nperseg, len(x))
    return signal.welch(x, fs=fs, window="hann", nperseg=nperseg, noverlap=nperseg // 2,
                        detrend="constant", scaling="density")


def frequency_resolution(fs: float, nperseg: int) -> float:
    return fs / nperseg


def band_energies(f: np.ndarray, pxx: np.ndarray, bands: list[tuple[float, float]]) -> list[float]:
    df = f[1] - f[0]
    out = []
    for lo, hi in bands:
        if not (0 <= lo < hi):
            raise ValueError(f"bad band {lo}-{hi}")
        m = (f >= lo) & (f < hi)
        out.append(float(np.sum(pxx[m]) * df))
    return out


def dominant_frequency(x: np.ndarray, fs: float, fmin: float = 1.0) -> float:
    x = _check(x, fs)
    xw = (x - x.mean()) * np.hanning(len(x))
    mag = np.abs(np.fft.rfft(xw))
    f = np.fft.rfftfreq(len(x), 1 / fs)
    mag[f < fmin] = 0
    k = int(np.argmax(mag))
    if 0 < k < len(mag) - 1:
        a, b, c = np.log(mag[k - 1] + 1e-30), np.log(mag[k] + 1e-30), np.log(mag[k + 1] + 1e-30)
        denom = a - 2 * b + c
        delta = 0.5 * (a - c) / denom if denom != 0 else 0.0
        return float((k + delta) * fs / len(x))
    return float(f[k])


def bearing_frequencies(shaft_hz: float, n_balls: int, ball_d: float, pitch_d: float,
                        contact_deg: float = 0.0) -> dict[str, float]:
    if shaft_hz <= 0 or n_balls < 1 or ball_d <= 0 or pitch_d <= ball_d:
        raise ValueError("invalid bearing geometry")
    r = (ball_d / pitch_d) * math.cos(math.radians(contact_deg))
    return {
        "bpfo": n_balls / 2 * shaft_hz * (1 - r),
        "bpfi": n_balls / 2 * shaft_hz * (1 + r),
        "bsf": pitch_d / (2 * ball_d) * shaft_hz * (1 - r ** 2),
        "ftf": shaft_hz / 2 * (1 - r),
    }


def envelope_spectrum(x: np.ndarray, fs: float, band: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    x = _check(x, fs, min_len=256)
    lo, hi = band
    if not (0 < lo < hi < fs / 2):
        raise ValueError(f"band {band} must lie inside (0, fs/2 = {fs / 2})")
    sos = signal.butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    y = signal.sosfiltfilt(sos, x)
    env = np.abs(signal.hilbert(y))
    env = (env - env.mean()) * np.hanning(len(env))
    mag = np.abs(np.fft.rfft(env)) * 2 / len(env)
    return np.fft.rfftfreq(len(env), 1 / fs), mag


@dataclass(frozen=True)
class FaultReport:
    bpfo_hz: float
    bpfi_hz: float
    bpfo_db: float
    bpfi_db: float
    fault: str | None  # "outer", "inner" or None


def _peak_db(f: np.ndarray, mag: np.ndarray, target: float, tol: float) -> float:
    hit = (f >= target * (1 - tol)) & (f <= target * (1 + tol))
    floor = (f >= target * 0.6) & (f <= target * 1.4) & ~hit
    if not hit.any() or not floor.any():
        return 0.0
    return float(20 * np.log10((mag[hit].max() + 1e-30) / (np.median(mag[floor]) + 1e-30)))


def detect_bearing_fault(x: np.ndarray, fs: float, shaft_hz: float, geometry: dict,
                         band: tuple[float, float] = (2_000.0, 4_500.0), tol: float = 0.03,
                         snr_db: float = 12.0) -> FaultReport:
    bf = bearing_frequencies(shaft_hz, **geometry)
    f, mag = envelope_spectrum(x, fs, band)
    scores = {}
    for name in ("bpfo", "bpfi"):
        fund = _peak_db(f, mag, bf[name], tol)
        harm = _peak_db(f, mag, 2 * bf[name], tol)
        scores[name] = (fund, fund >= snr_db and harm >= snr_db - 3)
    fault = None
    cands = [(scores[k][0], k) for k in scores if scores[k][1]]
    if cands:
        fault = {"bpfo": "outer", "bpfi": "inner"}[max(cands)[1]]
    return FaultReport(bf["bpfo"], bf["bpfi"], scores["bpfo"][0], scores["bpfi"][0], fault)
