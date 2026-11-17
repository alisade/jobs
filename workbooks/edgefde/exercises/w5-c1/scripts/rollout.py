"""Roll a model version out to the simulated 10-gateway fleet and print the report.

    python scripts/rollout.py v7            # good model
    python scripts/rollout.py v7-rev2bad    # fails only on the rev2 boards
    python scripts/rollout.py v7 --offline gw-05:40
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fleet.rollout import RolloutController  # noqa: E402
from fleet.sim import Fleet  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--offline", action="append", default=[], help="device:windows")
    ap.add_argument("--state", default="run/rollout-state.json")
    a = ap.parse_args()
    Path(a.state).parent.mkdir(parents=True, exist_ok=True)
    Path(a.state).unlink(missing_ok=True)
    f = Fleet()
    for spec in a.offline:
        dev, w = spec.split(":")
        f.take_offline(dev, int(w))
    c = RolloutController(f, a.state)
    c.start("v6", a.version)
    r = c.run()
    print(r)
    print("versions:", f.versions())
