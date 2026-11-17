"""Visible tests: the pipeline definition parses and a dry run succeeds."""

import json
import os

from simulate_run import simulate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPE = os.path.join(ROOT, "pipelines", "PL_Nightly_ERP_Load.DataPipeline", "pipeline-content.json")


def test_pipeline_json_parses():
    with open(PIPE) as f:
        d = json.load(f)
    assert d["properties"]["activities"], "no activities"


def test_dry_run_succeeds():
    run = simulate(PIPE)
    failed = [r for r in run["activityRuns"] if r["status"] == "Failed"]
    assert run["status"] == "Succeeded", failed[:1]
