"""Visible tests for w6-t1."""
from agent.guard import check_command


def test_plain_apply_denied():
    assert not check_command("terraform apply -auto-approve tfplan").allow


def test_chdir_apply_denied():
    assert not check_command("terraform -chdir=envs/stg apply -auto-approve /tmp/import.tfplan").allow


def test_plan_allowed():
    assert check_command("terraform -chdir=envs/stg plan -out=/tmp/import.tfplan").allow
