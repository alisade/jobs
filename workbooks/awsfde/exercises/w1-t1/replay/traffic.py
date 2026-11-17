"""Deterministic request traces for the Monday morning peak (08:50-09:20 UTC-5 local).

The 09:02 spike is the Monday login wave (the same every week). 2026-11-09 has ~20% more
traffic than 2026-11-02 after Brightline Health added two clinics.
"""

from __future__ import annotations

import random

WINDOW_S = 1800          # 08:50:00 - 09:20:00
START_LABEL = "08:50:00"
SPIKE_START, SPIKE_END = 720, 760   # 09:02:00 - 09:02:40


def base_rate(t: float) -> float:
    """Requests per second on the baseline Monday (2026-11-02)."""
    if t < 600:                       # ramp 08:50 - 09:00
        r = 1.2 + 2.55 * (t / 600)
    else:
        r = 3.75
    if SPIKE_START <= t < SPIKE_END:
        r *= 2.0
    return r


def trace(day: str, seed: int = 7) -> list[dict]:
    """One request per arrival: id, arrival time (s from 08:50), and whether its input is invalid."""
    growth = {"2026-11-02": 1.0, "2026-11-09": 1.2}[day]
    rng = random.Random(f"{day}-{seed}")
    out = []
    t = 0.0
    n = 0
    while t < WINDOW_S:
        rate = base_rate(t) * growth
        t += rng.expovariate(rate)
        if t >= WINDOW_S:
            break
        n += 1
        out.append({
            "request_id": f"{day.replace('-', '')}-{n:05d}",
            "arrival": round(t, 3),
            # ~1.5% of questions carry an attachment over the model's input limit -> ValidationException
            "invalid": rng.random() < 0.015,
            "latency": round(rng.uniform(1.8, 3.6), 3),
            "jitter_seed": rng.randrange(1 << 30),
        })
    return out


def clock(t: float) -> str:
    s = int(t) + 8 * 3600 + 50 * 60
    return f"{s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}"
