"""Confusion table for your detector over 10 synthetic captures per class."""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vib.features import bearing_frequencies, detect_bearing_fault, time_features  # noqa: E402
from vib.synth import bearing_signal  # noqa: E402

GEOM = dict(n_balls=9, ball_d=7.94, pitch_d=39.04, contact_deg=0.0)
bf = bearing_frequencies(29.5, **GEOM)
print(f"shaft 29.5 Hz: BPFO {bf['bpfo']:.2f} Hz, BPFI {bf['bpfi']:.2f} Hz, BSF {bf['bsf']:.2f} Hz, FTF {bf['ftf']:.2f} Hz")
for label, fhz, mod in [("healthy", None, False), ("outer", bf["bpfo"], False), ("inner", bf["bpfi"], True)]:
    c, kurt = Counter(), []
    for seed in range(100, 110):
        x = bearing_signal(fault_hz=fhz, seed=seed, fault_amp=0.6, modulate_by_shaft=mod)
        c[detect_bearing_fault(x, 20_000, 29.5, GEOM).fault] += 1
        kurt.append(time_features(x)["kurtosis"])
    print(f"{label:8} detected={dict(c)}  mean kurtosis={sum(kurt) / len(kurt):.2f}")
