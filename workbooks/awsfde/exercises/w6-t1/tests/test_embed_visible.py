"""Visible checks for w6-t1. The grader runs more."""

import replay


def test_no_blank_dashboards_and_no_cross_tenant_views(tmp_path):
    s = replay.run(str(tmp_path / "run"))
    assert s["views_of_another_tenants_data"] == 0
    assert s["blank_dashboards"] == 0
