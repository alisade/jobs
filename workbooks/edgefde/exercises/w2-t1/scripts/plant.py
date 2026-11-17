"""Raw 10 kHz captures for the Dunmore pumps (do not edit).

P01-P06: direct-drive pumps (2019). P07-P10: gearbox-driven pumps installed 2026-10-06; the
gearbox has a 44-tooth pinion on the 29.5 Hz shaft, gear mesh = 44 x 29.5 = 1298 Hz.
P03 has a confirmed outer-race defect (work order WO-55812, bearing replaced 2026-10-24).
"""

from __future__ import annotations

import numpy as np

FS_RAW = 10_000
SHAFT_HZ = 29.5
MESH_HZ = 44 * SHAFT_HZ
FAULT_MODE_HZ = 772.0
PUMPS = [f"P{i:02d}" for i in range(1, 11)]
GEARBOX = {"P07", "P08", "P09", "P10"}
FAULTY = {"P03"}


def capture(pump: str, seed: int = 0, seconds: float = 2.0, gain: float = 1.0) -> np.ndarray:
    rng = np.random.default_rng(int(pump[1:]) * 1000 + seed)
    n = int(FS_RAW * seconds)
    t = np.arange(n) / FS_RAW
    x = 0.5 * np.sin(2 * np.pi * SHAFT_HZ * t) + 0.2 * np.sin(2 * np.pi * 2 * SHAFT_HZ * t)
    x += rng.normal(0, 0.05, n)
    if pump in GEARBOX:
        x += 0.6 * np.sin(2 * np.pi * MESH_HZ * t + rng.uniform(0, 6.28))
    if pump in FAULTY:
        x += 0.25 * np.sin(2 * np.pi * FAULT_MODE_HZ * t) * (1 + 0.5 * np.sin(2 * np.pi * 105.75 * t))
    return gain * x
