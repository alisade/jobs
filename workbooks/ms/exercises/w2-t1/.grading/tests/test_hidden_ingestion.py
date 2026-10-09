import datetime as dt
import json
import pathlib
import re

import pytest

import simcheck as sim

EX = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
MAPPING = EX / "eventhouse" / "mappings" / "TelemetryLanding_mapping.json"
FUNC = EX / "eventhouse" / "functions" / "EnrichTelemetry.kql"

LANDING = [("Timestamp", "datetime"), ("DeviceId", "string"), ("VehicleId", "string"), ("SpeedKph", "real"),
           ("EngineTempC", "real"), ("FuelPct", "real"), ("FirmwareVersion", "string")]
ENRICHED = [c for c, _ in LANDING] + ["IsOverheating", "SpeedBand"]
UTC = dt.timezone.utc
EVENTS = [json.loads(x) for x in (HERE / "events_v2.jsonl").read_text().splitlines() if x.strip()]
EXPECTED = [
    {"Timestamp": dt.datetime(2026, 10, 20, 9, 20, 5, 123000, tzinfo=UTC), "DeviceId": "dev-9f1",
     "VehicleId": "TRK-100", "SpeedKph": 55.4, "EngineTempC": 88.2, "FuelPct": 71.5, "FirmwareVersion": "4.2.0"},
    {"Timestamp": dt.datetime(2026, 10, 20, 9, 21, 1, tzinfo=UTC), "DeviceId": "dev-c33",
     "VehicleId": "VAN-201", "SpeedKph": 0.0, "EngineTempC": 107.9, "FuelPct": 100.0, "FirmwareVersion": "4.2.0"},
    {"Timestamp": dt.datetime(2026, 10, 20, 9, 21, 59, 999000, tzinfo=UTC), "DeviceId": "dev-a07",
     "VehicleId": "TRK-102", "SpeedKph": 121.0, "EngineTempC": 91.0, "FuelPct": 3.5, "FirmwareVersion": "4.2.1-rc1"},
]


@pytest.fixture(scope="module")
def mapping():
    return json.loads(MAPPING.read_text())


def test_mapping_shape_valid(mapping):
    assert sim.validate_mapping(mapping, LANDING) == []


def test_every_landing_column_mapped_once(mapping):
    assert sorted(el["Column"] for el in mapping) == sorted(c for c, _ in LANDING)


def test_no_constant_values(mapping):
    assert not any("ConstValue" in el.get("Properties", {}) for el in mapping), \
        "ConstValue would hide the problem, not fix it"


@pytest.mark.parametrize("idx", range(len(EVENTS)))
def test_v2_event_maps_without_nulls(mapping, idx):
    row = sim.apply_mapping(EVENTS[idx], mapping, LANDING)
    nulls = [c for c, v in row.items() if v is None]
    assert not nulls, f"columns still null for a v2 event: {nulls}"


@pytest.mark.parametrize("idx", range(len(EVENTS)))
def test_v2_event_values_exact(mapping, idx):
    row = sim.apply_mapping(EVENTS[idx], mapping, LANDING)
    assert row == EXPECTED[idx]


def test_timestamp_uses_millisecond_transform(mapping):
    ts = [el for el in mapping if el["Column"] == "Timestamp"][0]["Properties"]
    assert ts.get("Transform") == "DateTimeFromUnixMilliseconds"


def _func_parts():
    text = re.sub(r"//[^\n]*", "", FUNC.read_text())
    body = re.search(r"EnrichTelemetry\(\)\s*\{(.*?)\n\}", text, re.S)
    pol = re.search(r"\.alter\s+table\s+TelemetryEnriched\s+policy\s+update\s*@'(.*?)'\s*$", text, re.S | re.M)
    return body.group(1) if body else "", pol.group(1) if pol else ""


def test_function_keeps_quality_filter():
    body, _ = _func_parts()
    flat = re.sub(r"\s+", "", body)
    assert "isnotempty(DeviceId)" in flat and "isnotnull(Timestamp)" in flat, \
        "the data-quality filter is correct; removing it would hide bad rows downstream"


def test_function_columns_exist():
    body, _ = _func_parts()
    assert body.strip().startswith("TelemetryLanding")
    defined = {c for c, _ in LANDING} | {"IsOverheating", "SpeedBand"}
    idents = set(re.findall(r"\b([A-Z][A-Za-z]+)\b", re.sub(r'"[^"]*"', "", body)))
    unknown = idents - defined - {"TelemetryLanding"}
    assert not unknown, f"function references columns that do not exist: {sorted(unknown)}"
    proj = re.search(r"\|\s*project\s+([^|]+)$", body.strip(), re.S)
    assert proj, "function must end with a project of the TelemetryEnriched columns"
    assert [x.strip() for x in proj.group(1).split(",")] == ENRICHED


def test_update_policy_still_transactional_and_enabled():
    _, pol = _func_parts()
    p = json.loads(pol)
    assert len(p) == 1
    p = p[0]
    assert p["IsEnabled"] is True and p["IsTransactional"] is True
    assert p["Source"] == "TelemetryLanding" and p["Query"].strip() == "EnrichTelemetry()"


def test_answer_names_the_schema_change():
    text = (EX / "ANSWER.md").read_text().lower()
    rc = text.split("## root cause", 1)[-1].split("## fix", 1)[0]
    assert "tsms" in rc and "device.id" in rc, "root cause should name the changed fields with evidence"
