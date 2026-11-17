"""Visible tests for w3-c1."""
import json
from pathlib import Path

import hcl2

import importgen

INV = Path(__file__).resolve().parents[1] / "inventory"


def gen():
    return importgen.generate(json.loads((INV / "cai-export.json").read_text())["assets"],
                              json.loads((INV / "state-ids.json").read_text()),
                              json.loads((INV / "projects.json").read_text()))


def blocks(res):
    out = {}
    for rel, text in res["files"].items():
        for imp in hcl2.loads(text).get("import", []):
            out[imp["to"].strip("${}")] = (rel, imp["id"])
    return out


def test_network_import_id_and_owner():
    b = blocks(gen())
    assert b["google_compute_network.riq_legacy"] == ("riq/imports.tf", "projects/tsl-riq-prod/global/networks/riq-legacy")


def test_subnetwork_import_id():
    b = blocks(gen())
    assert b["google_compute_subnetwork.riq_usc1"][1] == "projects/tsl-riq-prod/regions/us-central1/subnetworks/riq-usc1"


def test_output_parses():
    for text in gen()["files"].values():
        hcl2.loads(text)
