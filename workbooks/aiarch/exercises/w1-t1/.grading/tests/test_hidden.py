import json
import re
from pathlib import Path

import pytest
import yaml

from oidccheck import check

EX = Path.cwd()
PROD = "111100000004"
BASE = {"iss": "https://gitlab.com"}


def claims(ref_type, ref, project="harborpoint/lighthouse/platform", aud="https://gitlab.com"):
    return dict(BASE, aud=aud, project_path=project, ref=ref, ref_type=ref_type,
                sub=f"project_path:{project}:ref_type:{ref_type}:ref:{ref}")


def prod():
    return json.loads((EX / "trust/gitlab-deploy-prod.json").read_text())


@pytest.mark.parametrize("ref", ["v2.4.0", "v10.0.1"])
def test_release_tags_allowed(ref):
    ok, why = check(prod(), claims("tag", ref), PROD)
    assert ok, why


@pytest.mark.parametrize("ref_type,ref", [("branch", "main"), ("branch", "release/2.4"), ("tag", "nightly-2026-11-12")])
def test_non_release_refs_denied_for_prod(ref_type, ref):
    ok, _ = check(prod(), claims(ref_type, ref), PROD)
    assert not ok, f"{ref_type}:{ref} must not reach prod (CHG-8812: prod only from release tags)"


def test_other_project_tag_denied():
    ok, _ = check(prod(), claims("tag", "v2.4.0", project="harborpoint/lighthouse/platform-fork"), PROD)
    assert not ok


def test_other_group_tag_denied():
    ok, _ = check(prod(), claims("tag", "v2.4.0", project="someone-else/platform"), PROD)
    assert not ok


def test_audience_still_pinned():
    ok, _ = check(prod(), claims("tag", "v2.4.0", aud="https://attacker.example"), PROD)
    assert not ok


def test_dev_trust_unchanged_and_tight():
    dev = json.loads((EX / "trust/gitlab-deploy-dev.json").read_text())
    assert check(dev, claims("branch", "main"), "111100000003")[0]
    assert not check(dev, claims("tag", "v2.4.0"), "111100000003")[0]
    assert not check(dev, claims("branch", "feature/x"), "111100000003")[0]


def test_prod_pipeline_job_guarded():
    ci = yaml.safe_load((EX / ".gitlab-ci.yml").read_text())
    job = ci["deploy-prod"]
    assert job["environment"]["name"] == "production"
    rules = job["rules"]
    assert all("CI_COMMIT_TAG" in r.get("if", "") for r in rules), "prod job runs only for tags"
    assert any(r.get("when") == "manual" for r in rules), "prod deploy stays manual"
    assert re.search(r"arn:aws:iam::111100000004:role/gitlab-deploy-prod", job["variables"]["DEPLOY_ROLE_ARN"])


def test_oidc_template_unchanged_audience():
    ci = yaml.safe_load((EX / ".gitlab-ci.yml").read_text())
    assert ci[".aws-oidc"]["id_tokens"]["AWS_ID_TOKEN"]["aud"] == "https://gitlab.com"


def test_no_static_keys_in_pipeline():
    text = (EX / ".gitlab-ci.yml").read_text()
    assert "AKIA" not in text and "aws_secret_access_key" not in text.lower().replace("aws_secret_access_key=%s", "")


def test_answer_names_root_cause():
    text = (EX / "ANSWER.md").read_text().lower()
    assert "ref_type" in text and "tag" in text, "ANSWER.md should name the sub claim mismatch (ref_type tag vs branch)"
