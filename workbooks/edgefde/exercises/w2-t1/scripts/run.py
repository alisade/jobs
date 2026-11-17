"""Run the gateway pipeline over today's captures and print the alert board.

    python scripts/run.py [out_dir]   also writes out_dir/{alerts.log, firmware-changelog.txt, gateway.yaml}
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import plant  # noqa: E402
from edge.detector import detect  # noqa: E402
from edge.preprocess import FS_OUT, downsample  # noqa: E402


def board(seeds=range(3)) -> dict[str, list]:
    out = {}
    for p in plant.PUMPS:
        out[p] = [detect(downsample(plant.capture(p, s, gain=1.6)), FS_OUT) for s in seeds]
    return out


def main(out: Path | None) -> None:
    lines = []
    for p, vs in board().items():
        for i, v in enumerate(vs):
            ts = f"2026-10-27T0{6 + i}:00:00"
            lvl = "ALERT" if v.flagged else "ok   "
            lines.append(f"{ts} {lvl} pump={p} outer_race_band peak={v.peak_hz:.1f}Hz score={v.peak_db:.1f}dB")
    print("\n".join(lines))
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "alerts.log").write_text("\n".join(lines) + "\n")
        (out / "firmware-changelog.txt").write_text(
            "gateway firmware 3.4.0 (rolled out to all Dunmore gateways 2026-10-07)\n"
            "- accelerometer front end: range changed from +/-16 g to +/-8 g, gain x1.6 to use the ADC\n"
            "  resolution better (amplitudes in raw counts rise by 1.6x; scaled g values unchanged)\n"
            "- ntp: switch to the plant's internal NTP server\n"
            "- analytics: pipeline sample rate stays at 2 kHz (preprocess.downsample, factor 5)\n"
        )
        (out / "gateway.yaml").write_text(
            "sensor:\n  model: CVA-210 triaxial MEMS\n  sample_rate_hz: 10000\n  analog_antialias_filter: none (MEMS, digital output)\n"
            "analytics:\n  sample_rate_hz: 2000\n  detector: outer_race_band 600-900 Hz, threshold 25 dB\n"
            "assets:\n  P01-P06: direct drive, commissioned 2019\n  P07-P10: gearbox drive (44T pinion), commissioned 2026-10-06\n"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
