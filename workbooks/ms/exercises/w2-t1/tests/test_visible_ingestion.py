"""Visible checks: run with `make test`. The grader uses more events and checks exact values."""
import json
import pathlib
import sys

EX = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EX / "scripts"))
import sim  # noqa: E402

COLS = sim.load_schema(EX / "eventhouse" / "schema.kql")["TelemetryLanding"]
MAPPING = json.loads((EX / "eventhouse" / "mappings" / "TelemetryLanding_mapping.json").read_text())

V2_EVENT = {"schemaVersion": 2, "device": {"id": "dev-9f1", "fw": "4.2.0"}, "vehicleId": "TRK-100",
            "tsMs": 1792488005123, "telemetry": {"speedKph": 55.4, "engineTempC": 88.2, "fuelPct": 71.5}}


def test_mapping_is_valid():
    assert sim.validate_mapping(MAPPING, COLS) == []


def test_current_producer_event_lands_complete():
    row = sim.apply_mapping(V2_EVENT, MAPPING, COLS)
    assert all(v is not None for v in row.values()), row
