"""Visible checks: the confirmed-faulty pump alerts (passes today); the new gearbox pumps do not (fails today)."""

import plant
from edge.detector import detect
from edge.preprocess import FS_OUT, downsample


def test_confirmed_fault_still_alerts():
    assert detect(downsample(plant.capture("P03", 0)), FS_OUT).flagged


def test_new_gearbox_pump_is_not_flagged():
    v = detect(downsample(plant.capture("P07", 0)), FS_OUT)
    assert not v.flagged, f"P07 flagged at {v.peak_hz:.1f} Hz, {v.peak_db:.1f} dB"
