import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import appset_sim  # noqa: E402


def rows():
    return appset_sim.render(ROOT / "argocd/applicationsets", ROOT / "argocd/clusters", ROOT / "charts/index.yaml")


def test_canary_clusters_get_3_0_0():
    got = {r["cluster"]: r["resolved"] for r in rows()}
    assert got["dev-1"] == "3.0.0" and got["stg-1"] == "3.0.0"


def test_prod_clusters_stay_on_2x_after_3_0_0_is_published():
    got = {r["cluster"]: r["resolved"] for r in rows()}
    for c in ("prod-blue", "prod-green"):
        assert got[c].startswith("2."), f"{c} resolved to {got[c]}; stable must not follow a new major"
