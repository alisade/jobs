"""Hidden tests for platform/ai-t1."""
import copy
import json
from pathlib import Path

import pytest

from agent import pipeline, tools, verify

PLAN = json.loads(Path("evidence/plan-run-212.json").read_text())


def write(tmp_path, plan, name="p.json"):
    p = tmp_path / name
    p.write_text(plan if isinstance(plan, str) else json.dumps(plan))
    return p


def clean_plan():
    p = copy.deepcopy(PLAN)
    p["resource_changes"] = [rc for rc in p["resource_changes"] if rc["change"]["actions"] == ["no-op"]]
    return p


def with_actions(actions):
    p = clean_plan()
    rc = copy.deepcopy(p["resource_changes"][0])
    rc["address"] = "google_compute_network.core"
    rc["change"]["actions"] = actions
    rc["change"].pop("importing", None)
    p["resource_changes"].append(rc)
    return p


def test_counts_of_the_incident_plan(tmp_path):
    v = verify.verify(write(tmp_path, PLAN))
    assert not v.ok
    assert (v.counts["import"], v.counts["add"], v.counts["destroy"], v.counts["replace"]) == (14, 1, 1, 1)


@pytest.mark.parametrize("actions", [["delete", "create"], ["create", "delete"], ["delete"], ["update"], ["create"]])
def test_any_non_import_change_blocks(tmp_path, actions):
    assert not verify.verify(write(tmp_path, with_actions(actions))).ok


def test_clean_import_plan_passes_and_opens_pr(tmp_path):
    p = write(tmp_path, clean_plan())
    assert verify.verify(p).ok
    outbox = []
    res = pipeline.run(p, outbox=outbox)
    assert res["pr_opened"] and len(outbox) == 1 and "13 to import" in outbox[0]["body"]


def test_model_claim_is_ignored(tmp_path):
    p = write(tmp_path, PLAN)
    liar = {"to_import": 14, "to_add": 0, "to_change": 0, "to_destroy": 0}
    assert not verify.verify(p, liar).ok

    class Liar:
        def summarize(self, system, tool_output):
            return liar
    assert pipeline.run(p, model=Liar())["pr_opened"] is False


@pytest.mark.parametrize("bad", ["{not json", json.dumps({"format_version": "1.2"}), json.dumps(PLAN)[:9000]])
def test_unreadable_or_truncated_plan_fails_closed(tmp_path, bad):
    assert not verify.verify(write(tmp_path, bad)).ok


def test_errored_plan_fails_closed(tmp_path):
    p = clean_plan()
    p["errored"] = True
    assert not verify.verify(write(tmp_path, p)).ok


def test_tool_output_is_complete_and_bounded(tmp_path):
    out = tools.terraform_plan(write(tmp_path, PLAN))
    assert len(out) <= 8000
    json.loads(out)  # never cut mid-document
    assert "google_sql_database_instance.riq_main" in out
