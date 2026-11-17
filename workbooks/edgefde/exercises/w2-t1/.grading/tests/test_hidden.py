"""Hidden tests for edgefde/w2-t1: aliasing removed, real content kept, interface unchanged."""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import plant  # noqa: E402
from edge.detector import detect  # noqa: E402
from edge.preprocess import FS_OUT, FS_RAW, downsample  # noqa: E402


def tone_db(y, fs, f0):
    w = np.hanning(len(y))
    mag = np.abs(np.fft.rfft(y * w)) * 2 / w.sum()
    f = np.fft.rfftfreq(len(y), 1 / fs)
    m = np.abs(f - f0) < 3
    return 20 * np.log10(mag[m].max() + 1e-12)


@pytest.mark.parametrize("pump", sorted(plant.GEARBOX))
@pytest.mark.parametrize("seed", [0, 5])
def test_gearbox_pumps_clean(pump, seed):
    assert not detect(downsample(plant.capture(pump, seed, gain=1.6)), FS_OUT).flagged


@pytest.mark.parametrize("seed", [0, 1, 2, 7])
def test_faulty_pump_still_flagged(seed):
    v = detect(downsample(plant.capture("P03", seed, gain=1.6)), FS_OUT)
    assert v.flagged and abs(v.peak_hz - 772) < 3


def test_out_of_band_tone_attenuated_40db():
    t = np.arange(20_000) / FS_RAW
    y = downsample(np.sin(2 * np.pi * 1298 * t))
    assert tone_db(y, FS_OUT, 702) < -40, "1298 Hz must not fold to 702 Hz"


def test_in_band_tone_preserved():
    t = np.arange(20_000) / FS_RAW
    for f0 in (100.0, 300.0, 772.0):
        assert abs(tone_db(downsample(np.sin(2 * np.pi * f0 * t)), FS_OUT, f0)) < 1.0, f0


def test_output_rate_and_length():
    y = downsample(np.zeros(20_000))
    assert len(y) == 4_000


def test_detector_and_rates_untouched():
    import edge.detector as d

    assert d.BAND == (600.0, 900.0) and d.THRESHOLD_DB == 25.0
    assert FS_RAW == 10_000 and FS_OUT == 2_000


def test_direct_drive_pumps_quiet():
    for p in ["P01", "P02", "P04", "P05", "P06"]:
        assert not detect(downsample(plant.capture(p, 3, gain=1.6)), FS_OUT).flagged, p
