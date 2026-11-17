"""In-process simulated gateway fleet with a fake clock (complete: do not edit).

Each gateway runs one model version. You change what it should run with
fleet.set_desired(device_id, version); an online gateway applies it on the next
tick (one window), an offline one when it comes back. Every tick each online
gateway produces a Health report for that window; offline gateways produce None.

How a model behaves is defined in MODELS: process up or crash-looping, inference
error rate, p95 latency and the alert rate it produces per window. Some models
behave differently on hardware revision rev2 (gw-07..gw-10, newer CPU board).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

MODELS: dict[str, dict] = {
    "v6": {"up": True, "error_rate": 0.001, "p95_ms": 18.0, "alert_rate": 0.02},
    "v7": {"up": True, "error_rate": 0.001, "p95_ms": 16.0, "alert_rate": 0.02},
    "v7-crash": {"up": False, "error_rate": 1.0, "p95_ms": 0.0, "alert_rate": 0.0},
    "v7-storm": {"up": True, "error_rate": 0.002, "p95_ms": 17.0, "alert_rate": 0.40},
    "v7-slow": {"up": True, "error_rate": 0.001, "p95_ms": 95.0, "alert_rate": 0.02},
    # fine on rev1 boards, uses an operator the rev2 board's runtime build lacks: inference errors
    "v7-rev2bad": {"up": True, "error_rate": 0.001, "p95_ms": 16.0, "alert_rate": 0.02,
                   "rev2": {"error_rate": 0.35}},
}


@dataclass(frozen=True)
class Health:
    device_id: str
    window: int
    version: str
    up: bool
    error_rate: float
    p95_ms: float
    alert_rate: float


@dataclass
class Device:
    device_id: str
    hw: str
    version: str
    desired: str
    online: bool = True
    history: list[str] = field(default_factory=list)


class Fleet:
    def __init__(self, n: int = 10, version: str = "v6", seed: int = 0) -> None:
        self.window = 0
        self.rng = random.Random(seed)
        self.devices: dict[str, Device] = {}
        for i in range(1, n + 1):
            did = f"gw-{i:02d}"
            self.devices[did] = Device(did, "rev2" if i >= 7 else "rev1", version, version)
        self.offline_until: dict[str, int] = {}
        self.desired_calls: list[tuple[int, str, str]] = []
        self.last: dict[str, Health | None] = {}

    # ---- control plane ---------------------------------------------------------------
    def set_desired(self, device_id: str, version: str) -> None:
        if version not in MODELS:
            raise KeyError(f"unknown model version {version}")
        self.devices[device_id].desired = version
        self.desired_calls.append((self.window, device_id, version))

    def ids(self) -> list[str]:
        return sorted(self.devices)

    # ---- fault injection (tests and scripts) ----------------------------------------------
    def take_offline(self, device_id: str, windows: int) -> None:
        self.devices[device_id].online = False
        self.offline_until[device_id] = self.window + windows

    # ---- simulation -------------------------------------------------------------------
    def _behaviour(self, d: Device) -> dict:
        b = dict(MODELS[d.version])
        b.update(b.pop("rev2", {}) if d.hw == "rev2" else {})
        b.pop("rev2", None)
        return b

    def tick(self) -> dict[str, Health | None]:
        """Advance one window; return this window's report per device (None = offline)."""
        self.window += 1
        out: dict[str, Health | None] = {}
        for did in self.ids():
            d = self.devices[did]
            if not d.online and self.window >= self.offline_until.get(did, 0):
                d.online = True
            if not d.online:
                out[did] = None
                continue
            if d.version != d.desired:
                d.version = d.desired
                d.history.append(d.version)
            b = self._behaviour(d)
            jitter = 1 + self.rng.uniform(-0.05, 0.05)
            out[did] = Health(did, self.window, d.version, b["up"], min(1.0, b["error_rate"] * jitter),
                              b["p95_ms"] * jitter, b["alert_rate"] * jitter)
        self.last = out
        return out

    def versions(self) -> dict[str, str]:
        return {did: d.version for did, d in self.devices.items()}
