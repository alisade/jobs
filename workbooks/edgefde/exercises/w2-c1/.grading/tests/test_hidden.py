"""Hidden tests for edgefde/w2-c1."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vib import features as F  # noqa: E402
from vib.synth import bearing_signal, tones  # noqa: E402

GEOM = dict(n_balls=9, ball_d=7.94, pitch_d=39.04, contact_deg=0.0)
FS = 20_000


def test_gaussian_kurtosis_is_about_three():
    x = np.random.default_rng(1).normal(0, 1, 200_000)
    assert F.time_features(x)["kurtosis"] == pytest.approx(3.0, abs=0.05)


def test_dc_offset_does_not_change_ac_features():
    a = F.time_features(tones(5000, 1, [(80, 1)]))
    b = F.time_features(tones(5000, 1, [(80, 1)], dc=3.0))
    for k in a:
        assert b[k] == pytest.approx(a[k], rel=1e-6), k


def test_impulsive_signal_high_crest_and_kurtosis():
    x = np.random.default_rng(2).normal(0, 0.1, 20_000)
    x[::2000] += 5
    tf = F.time_features(x)
    assert tf["kurtosis"] > 20 and tf["crest_factor"] > 10


def test_nperseg_capped_at_window_length():
    f, pxx = F.welch_psd(tones(2000, 0.5, [(100, 1)]), 2000, nperseg=4096)
    assert f[1] - f[0] == pytest.approx(2000 / 1000)


def test_band_energy_of_a_sine_is_its_power():
    f, pxx = F.welch_psd(tones(10_000, 4, [(1_234, 3.0)]), 10_000, nperseg=2048)
    e = F.band_energies(f, pxx, [(0, 1000), (1000, 1500), (1500, 5000)])
    assert e[1] == pytest.approx(3.0 ** 2 / 2, rel=0.05)
    assert e[0] < 0.01 * e[1] and e[2] < 0.01 * e[1]


def test_dominant_frequency_sub_bin_and_ignores_dc():
    x = tones(1000, 1.0, [(123.4, 1.0)], noise=0.05, dc=10.0)
    assert F.dominant_frequency(x, 1000) == pytest.approx(123.4, abs=0.25)  # bin = 1 Hz


def test_dominant_frequency_picks_stronger_of_close_tones():
    x = tones(2000, 2.0, [(300.0, 1.0), (304.0, 0.5)])
    assert F.dominant_frequency(x, 2000) == pytest.approx(300.0, abs=0.3)


def test_bearing_frequency_identities_and_contact_angle():
    bf = F.bearing_frequencies(25.0, 12, 10.0, 50.0, 15.0)
    assert bf["bpfo"] + bf["bpfi"] == pytest.approx(12 * 25.0)
    r = 0.2 * math.cos(math.radians(15))
    assert bf["ftf"] == pytest.approx(12.5 * (1 - r))
    assert bf["bsf"] == pytest.approx(50 / 20 * 25 * (1 - r ** 2))


@pytest.mark.parametrize("bad", [dict(shaft_hz=0), dict(n_balls=0), dict(ball_d=50.0)])
def test_bearing_frequencies_rejects_bad_geometry(bad):
    args = dict(shaft_hz=29.5, **GEOM)
    args.update(bad)
    with pytest.raises(ValueError):
        F.bearing_frequencies(**args)


@pytest.mark.parametrize("seed", range(6))
def test_healthy_not_flagged(seed):
    assert F.detect_bearing_fault(bearing_signal(seed=seed), FS, 29.5, GEOM).fault is None


@pytest.mark.parametrize("seed", range(3))
def test_inner_race_fault(seed):
    bf = F.bearing_frequencies(29.5, **GEOM)
    x = bearing_signal(fault_hz=bf["bpfi"], seed=seed, fault_amp=0.8, modulate_by_shaft=True)
    assert F.detect_bearing_fault(x, FS, 29.5, GEOM).fault == "inner"


def test_weak_outer_fault_still_found():
    bf = F.bearing_frequencies(29.5, **GEOM)
    x = bearing_signal(fault_hz=bf["bpfo"], seed=11, fault_amp=0.4)
    r = F.detect_bearing_fault(x, FS, 29.5, GEOM)
    assert r.fault == "outer" and r.bpfo_db > 12


def test_band_above_nyquist_rejected():
    with pytest.raises(ValueError):
        F.envelope_spectrum(bearing_signal(fs=8000), 8000, (2000, 4500))


@pytest.mark.parametrize("bad", [np.array([1.0, np.nan] * 500), np.ones(10), np.ones((10, 100))])
def test_input_validation(bad):
    with pytest.raises(ValueError):
        F.time_features(bad)


def test_fs_must_be_positive():
    with pytest.raises(ValueError):
        F.welch_psd(np.ones(1000), 0)
