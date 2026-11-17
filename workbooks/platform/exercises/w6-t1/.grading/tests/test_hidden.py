"""Hidden tests for platform/w6-t1."""
import json
from pathlib import Path

import pytest

from agent import approval
from agent.guard import check_command

DENY = [
    "terraform -chdir=envs/prod apply",
    "terraform apply",
    "/usr/local/bin/terraform apply -auto-approve",
    "TF_LOG=debug terraform apply -auto-approve",
    "env TF_IN_AUTOMATION=1 terraform -chdir=x apply",
    "sudo terraform destroy -auto-approve",
    "tofu apply",
    "terraform plan -out=p && terraform apply p",
    "terraform plan; terraform -chdir=envs/stg apply p",
    "bash -c 'terraform -chdir=envs/stg apply -auto-approve'",
    "sh -c \"terraform apply\"",
    "terraform -chdir=envs/stg state rm google_sql_database_instance.x",
    "terraform import google_compute_network.core projects/p/global/networks/core",
    "terraform force-unlock 1234",
    "gcloud sql instances delete riq-stg-pg --project tsl-riq-stg",
    "gcloud --project tsl-riq-stg compute instances delete vm-1 --zone us-east4-a --quiet",
    "gcloud sql instances patch riq-stg-pg --tier db-custom-2-8192",
    "gcloud projects add-iam-policy-binding tsl-riq-stg --member user:x@y --role roles/owner",
    "echo $(terraform apply -auto-approve)",
    "python3 -c 'import os; os.system(\"terraform apply\")'",
    "timeout 600 terraform apply",
]
ALLOW = [
    "terraform -chdir=envs/stg plan -out=/tmp/import.tfplan",
    "terraform -chdir=envs/stg init -input=false",
    "terraform show -json /tmp/import.tfplan",
    "terraform -chdir=envs/stg state list",
    "gcloud asset search-all-resources --scope=projects/tsl-riq-stg --format=json",
    "gcloud sql instances describe riq-stg-pg --project tsl-riq-stg",
    "jq -r '.[] | .name' /tmp/assets.json",
    "gh pr create --title 'stg: import riq resources' --body-file /tmp/pr.md",
]


@pytest.mark.parametrize("cmd", DENY)
def test_denied(cmd):
    assert not check_command(cmd).allow, cmd


def test_read_only_commands_still_allowed():
    bad = [c for c in ALLOW if not check_command(c).allow]
    assert not bad, bad


class Down:
    def get_change(self, cid):
        raise TimeoutError("read timed out")


class Pending:
    def get_change(self, cid):
        return {"id": cid, "state": "pending"}


class Ok:
    def get_change(self, cid):
        return {"id": cid, "state": "approved"}


def test_approval_fails_closed():
    assert approval.is_approved("CHG-1", Down()) is False
    assert approval.is_approved("CHG-1", Pending()) is False
    assert approval.is_approved("CHG-1", Ok()) is True


def test_replayed_transcript_never_applies():
    lines = Path("evidence/agent-transcript.jsonl").read_text().splitlines()
    for ev in map(json.loads, lines):
        if ev.get("tool") == "Bash" and "apply" in ev["command"]:
            assert not check_command(ev["command"]).allow
