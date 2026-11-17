from helpers import claims, policy

from oidccheck import check

PROD = "111100000004"


def test_release_tag_can_assume_prod_role():
    ok, why = check(policy("gitlab-deploy-prod"), claims("tag", "v2.4.0"), PROD)
    assert ok, why


def test_main_still_deploys_dev():
    ok, why = check(policy("gitlab-deploy-dev"), claims("branch", "main"), "111100000003")
    assert ok, why


def test_feature_branch_cannot_assume_prod_role():
    ok, _ = check(policy("gitlab-deploy-prod"), claims("branch", "feature/new-tool"), PROD)
    assert not ok
