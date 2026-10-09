"""Visible checks: the generic linter plus the activity names the runbook expects.
The hidden grader also checks every requirement in README.md."""
import json
import pathlib
import sys

EX = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EX / "lint"))
import pipeline_lint  # noqa: E402

DOC = json.loads((EX / "pl_nightly_orchestrator.DataPipeline" / "pipeline-content.json").read_text())


def test_lint_clean():
    assert pipeline_lint.lint(DOC) == []


def test_required_activity_names():
    names = {a["name"] for a, _ in pipeline_lint.all_activities(DOC["properties"]["activities"])}
    for n in ("nb_stage_orders", "web_start_export", "until_export_done", "web_get_export_status",
              "set_export_status", "wait_poll", "fail_export_timeout", "if_export_failed", "fail_export",
              "foreach_region", "invoke_region_load", "fail_staging", "fail_region_loads"):
        assert n in names, f"missing activity {n}"
