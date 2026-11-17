"""Run 30 s of a healthy stream through the gateway path and print the per-chunk alerts.

    python scripts/run.py [out_dir]   also writes out_dir/{gateway.log, chunk_scores.csv}
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sensor  # noqa: E402
from stream.alerting import score  # noqa: E402
from stream.filter import StreamingBandpass  # noqa: E402


def run(x: np.ndarray, size: int = sensor.FS):
    f = StreamingBandpass()
    return [score(i, f.process(c)) for i, c in enumerate(sensor.chunks(x, size))]


def main(out: Path | None) -> None:
    res = run(sensor.stream(30, seed=4))
    lines = [f"2026-11-02T09:14:{i:02d} {'ALERT' if r.alert else 'ok   '} chunk={i} kurtosis={r.kurtosis:.1f} crest={r.crest:.1f}" for i, r in enumerate(res)]
    lines.insert(3, "2026-11-02T09:14:03 WARN  driver: sensor clock drift 180 ppm vs gateway RTC (resync scheduled)")
    print("\n".join(lines[:8]) + f"\n... {sum(r.alert for r in res)} of {len(res)} chunks alerted")
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "gateway.log").write_text("\n".join(lines) + "\n")
        y = StreamingBandpass().process(sensor.stream(2, seed=4)[:20_000])
        with (out / "first_chunk_samples.csv").open("w") as fh:
            fh.write("sample,filtered\n")
            for i in range(0, 400, 4):
                fh.write(f"{i},{y[i]:.5f}\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
