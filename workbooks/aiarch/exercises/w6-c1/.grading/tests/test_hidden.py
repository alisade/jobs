import json

import pytest
import yaml

from fakes import ROOT, RUNTIME, World, execute
from ssmsim import ParameterError


def doc():
    return yaml.safe_load((ROOT / "runbooks/rollback-agent-endpoint.yaml").read_text())


def test_backup_contains_previous_version_and_execution_id():
    w = World(live="9")
    execute(w)
    (key, body), = w.objects.items()
    assert key.startswith(f"rollback/{RUNTIME}/prod/") and "exec-0001" in key
    assert json.loads(body)["liveVersion"] == "9"


def test_rejected_approval_changes_nothing():
    w = World(live="9")
    r = execute(w, approve=lambda i: False)
    assert r["status"] == "Failed"
    assert "UpdateAgentRuntimeEndpoint" not in w.apis() and w.live == "9"


def test_approval_step_names_approvers_and_versions():
    seen = {}
    w = World(live="9")
    execute(w, approve=lambda i: seen.update(i) or True)
    assert seen.get("Approvers") and int(seen.get("MinRequiredApprovals", 0)) >= 1
    assert "9" in seen.get("Message", "") and "7" in seen.get("Message", "")


def test_waits_for_ready():
    w = World(live="9", ready_after=3)
    r = execute(w)
    assert r["status"] == "Success"
    assert w.apis().count("GetAgentRuntimeEndpoint") >= 3


def test_wait_timeout_fails():
    w = World(live="9", never_ready=True)
    r = execute(w)
    assert r["status"] == "Failed" and "Wait" in (r["failed_step"] or "") or "timed out" in (r["error"] or "")
    assert "GetMetricStatistics" not in w.apis()


def test_high_errors_fail_the_execution():
    w = World(live="9", errors=40)
    r = execute(w)
    assert r["status"] == "Failed" and "GetMetricStatistics" in w.apis()


def test_threshold_is_a_parameter():
    w = World(live="9", errors=40)
    assert execute(w, ErrorThreshold=50)["status"] == "Success"


def test_already_at_target_is_a_no_op():
    w = World(live="7")
    asked = []
    r = execute(w, approve=lambda i: asked.append(1) or True)
    assert r["status"] == "Success"
    assert "UpdateAgentRuntimeEndpoint" not in w.apis() and not asked and not w.objects


@pytest.mark.parametrize("bad", [{"TargetVersion": "latest"}, {"TargetVersion": "7; rm"}, {"AgentRuntimeId": "../x"},
                                 {"AutomationAssumeRole": "admin"}])
def test_parameter_validation(bad):
    with pytest.raises(ParameterError):
        execute(World(), **bad)


def test_runbook_shape():
    d = doc()
    assert str(d["schemaVersion"]) == "0.3" and "AutomationAssumeRole" in d["assumeRole"]
    actions = [s["action"] for s in d["mainSteps"]]
    for a in ("aws:executeAwsApi", "aws:approve", "aws:waitForAwsResourceProperty", "aws:branch"):
        assert a in actions
    wait = [s for s in d["mainSteps"] if s["action"] == "aws:waitForAwsResourceProperty"][0]
    assert int(wait.get("timeoutSeconds", 3600)) <= 900


def test_outputs_expose_previous_version():
    r = execute(World(live="9"))
    assert "9" in [str(v) for v in r["outputs"].values()]
