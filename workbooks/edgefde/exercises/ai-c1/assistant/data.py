"""Read-only fixture data the tools serve (complete: do not edit)."""

from __future__ import annotations

ALERTS = [
    {"id": "A-1042", "machine": "P04", "ts": "2026-11-12T14:05:00Z", "kind": "outer_race", "score_db": 18.4,
     "note": "Vibration rising since Monday; contractor route reading 4.1 mm/s."},
    {"id": "A-1043", "machine": "P04", "ts": "2026-11-12T15:05:00Z", "kind": "outer_race", "score_db": 19.1, "note": ""},
    {"id": "A-1038", "machine": "P07", "ts": "2026-11-11T09:00:00Z", "kind": "outer_race", "score_db": 13.0,
     "note": "Closed: aliasing artefact, fixed in preprocess 2026-10-28."},
]

FEATURES = {
    "P04": [
        {"window_start": "2026-11-12T13:00:00Z", "rms": 0.61, "kurtosis": 3.4, "bpfo_db": 9.0},
        {"window_start": "2026-11-12T14:00:00Z", "rms": 0.74, "kurtosis": 5.8, "bpfo_db": 17.9},
        {"window_start": "2026-11-12T15:00:00Z", "rms": 0.78, "kurtosis": 6.1, "bpfo_db": 19.0},
    ],
    "P07": [
        {"window_start": "2026-11-11T09:00:00Z", "rms": 0.42, "kurtosis": 3.0, "bpfo_db": 4.2},
    ],
}

MODEL_CARD = {
    "model": "pump-health", "version": "v7", "type": "IsolationForest on spectral features, INT8 ONNX",
    "trained_on": "2026-10-01..2026-10-31, 4 pumps", "recall_holdout": 0.86, "false_alarms_per_machine_week": 0.08,
    "limitations": "Not validated for seal or motor faults; shaft speed assumed 29.5 Hz.",
}

RAW_CAPTURES = {"P04": {"fs": 20000, "samples": [0.01 * (i % 17) for i in range(2000)]}}
