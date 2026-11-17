"""Visible tests: known-answer checks on synthetic signals."""

import math

import numpy as np
import pytest

from vib import features as F
from vib.synth import bearing_signal, tones

GEOM = dict(n_balls=9, ball_d=7.94, pitch_d=39.04, contact_deg=0.0)  # 6205-class deep-groove bearing


def test_sine_time_features():
    tf = F.time_features(tones(10_000, 1.0, [(50, 2.0)]))
    assert tf["rms"] == pytest.approx(2 / math.sqrt(2), rel=1e-3)
    assert tf["crest_factor"] == pytest.approx(math.sqrt(2), rel=1e-3)
    assert tf["kurtosis"] == pytest.approx(1.5, abs=0.01)


def test_welch_resolution():
    f, pxx = F.welch_psd(tones(1000, 8, [(120, 1)], noise=0.1), 1000, nperseg=1000)
    assert f[1] - f[0] == pytest.approx(1.0)
    assert F.frequency_resolution(1000, 1000) == pytest.approx(1.0)
    assert f[np.argmax(pxx)] == pytest.approx(120, abs=1)


def test_bearing_frequencies_6205():
    bf = F.bearing_frequencies(29.5, **GEOM)
    assert bf["bpfo"] == pytest.approx(105.75, abs=0.05)
    assert bf["bpfi"] == pytest.approx(159.75, abs=0.05)


def test_outer_race_fault_detected():
    bf = F.bearing_frequencies(29.5, **GEOM)
    r = F.detect_bearing_fault(bearing_signal(fault_hz=bf["bpfo"], seed=3, fault_amp=0.8), 20_000, 29.5, GEOM)
    assert r.fault == "outer"
