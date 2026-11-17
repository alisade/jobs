"""Hidden tests for edgefde/x-2: chunked filtering equals one-shot causal filtering."""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run  # noqa: E402
import sensor  # noqa: E402
from stream.filter import StreamingBandpass  # noqa: E402


def reference(x):
    f = StreamingBandpass()
    return signal.sosfilt(f.sos, x, zi=signal.sosfilt_zi(f.sos) * x[0])[0]


@pytest.mark.parametrize("size", [20_000, 4_096, 777])
def test_chunked_equals_one_shot(size):
    x = sensor.stream(5, seed=2)
    f = StreamingBandpass()
    y = np.concatenate([f.process(c) for c in sensor.chunks(x, size)])
    assert np.max(np.abs(y - reference(x))) < 1e-9


def test_causal_not_zero_phase():
    """An impulse must not produce output before it arrives (filtfilt would)."""
    x = np.ones(4000)
    x[2000] += 1.0
    f = StreamingBandpass()
    y = np.concatenate([f.process(x[:2500]), f.process(x[2500:])])
    assert np.max(np.abs(y[:2000])) < 1e-6


def test_no_transient_at_chunk_edges():
    x = sensor.stream(4, seed=3)
    f = StreamingBandpass()
    y = np.concatenate([f.process(c) for c in sensor.chunks(x)])
    edge = np.max(np.abs(y[19_990:20_050]))
    body = np.max(np.abs(y[30_000:39_000]))
    assert edge < 2 * body


@pytest.mark.parametrize("seed", [0, 4, 9])
def test_healthy_quiet(seed):
    assert sum(r.alert for r in run.run(sensor.stream(15, seed=seed))) == 0


def test_fault_still_alerts():
    assert all(r.alert for r in run.run(sensor.stream(8, seed=5, fault_hz=105.75)))


def test_reset_restarts_history():
    x = sensor.stream(2, seed=6)
    f = StreamingBandpass()
    f.process(x[:20_000])
    f.reset()
    y = f.process(x[20_000:])
    assert np.max(np.abs(y - reference(x[20_000:]))) < 1e-9


def test_empty_chunk_ok():
    f = StreamingBandpass()
    assert len(f.process(np.array([]))) == 0
