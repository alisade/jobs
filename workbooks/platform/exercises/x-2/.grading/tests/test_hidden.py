"""Hidden checks for platform/x-2. They use a private copy of the simulator, so editing
tools/appset_sim.py cannot change the result."""
import pathlib
import re
import shutil
import sys

import yaml

CWD = pathlib.Path.cwd()
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sim_ref as sim  # noqa: E402

APPSETS = CWD / "argocd" / "applicationsets"
CLUSTERS = CWD / "argocd" / "clusters"
INDEX = CWD / "charts" / "index.yaml"
FUTURE = HERE / "fixtures" / "index-future.yaml"


def by_cluster(index=INDEX, clusters=CLUSTERS):
    out = {}
    for r in sim.render(APPSETS, clusters, index):
        out.setdefault(r["cluster"], []).append(r)
    return out


def test_today_prod_resolves_2_4_1_or_newer_2x():
    got = by_cluster()
    for c in ("prod-blue", "prod-green"):
        assert len(got[c]) == 1
        v = got[c][0]["resolved"]
        assert re.match(r"^2\.\d+\.\d+$", v), f"{c}: {v}"
        assert sim.vkey(sim.parse_version(v)) >= sim.vkey(sim.parse_version("2.4.1")), f"{c} must not roll back below 2.4.1: {v}"


def test_future_index_stable_never_takes_a_new_major():
    got = by_cluster(FUTURE)
    for c in ("prod-blue", "prod-green"):
        v = got[c][0]["resolved"]
        assert v.startswith("2."), f"with 3.1.0 published, {c} resolved {v}"


def test_future_index_canary_stays_on_3x_release():
    got = by_cluster(FUTURE)
    for c in ("dev-1", "stg-1"):
        v = got[c][0]["resolved"]
        assert re.match(r"^3\.\d+\.\d+$", v), f"{c}: {v} (no pre-releases, major 3)"


def test_every_cluster_exactly_once():
    rows = sim.render(APPSETS, CLUSTERS, INDEX)
    cov = sim.coverage(rows, CLUSTERS)
    assert all(n == 1 for n in cov.values()), cov


def test_new_cluster_without_wave_label_is_covered_once(tmp_path):
    d = tmp_path / "clusters"
    shutil.copytree(CLUSTERS, d)
    (d / "prod-blue-2.yaml").write_text(yaml.safe_dump({
        "apiVersion": "v1", "kind": "Secret",
        "metadata": {"name": "cluster-prod-blue-2", "namespace": "argocd",
                     "labels": {"argocd.argoproj.io/secret-type": "cluster", "env": "prod", "fleet": "tsl-fleet-host"}},
        "stringData": {"name": "prod-blue-2", "server": "https://10.41.0.2"}}))
    rows = sim.render(APPSETS, d, INDEX)
    cov = sim.coverage(rows, d)
    assert cov["prod-blue-2"] == 1, cov
    got = [r for r in rows if r["cluster"] == "prod-blue-2"][0]
    assert got["resolved"].startswith("2."), "an unlabelled new cluster must get the stable version"


def test_application_names_and_values_unchanged():
    got = by_cluster()
    for c, env in (("dev-1", "dev"), ("stg-1", "stg"), ("prod-blue", "prod"), ("prod-green", "prod")):
        r = got[c][0]
        assert r["application"] == f"{c}-riq-api", "renaming Applications orphans the live ones"
        assert r["valueFiles"] == [f"values-{env}.yaml"]


def test_no_resolution_errors():
    for r in sim.render(APPSETS, CLUSTERS, FUTURE):
        assert not r["resolved"].startswith("ERROR"), r


def _section(text, name):
    m = re.search(r"^## " + re.escape(name) + r"\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return re.sub(r"(?s)<!--.*?-->", "", m.group(1)) if m else ""


def test_answer_root_cause_names_the_range():
    text = (CWD / "ANSWER.md").read_text()
    rc = _section(text, "Root cause")
    assert ">=2.0.0" in rc, "quote the unbounded targetRevision in Root cause"
    assert "3.0.0" in rc
    assert re.search(r"selfheal|self-heal|self heal", rc, re.I), "say why selfHeal is or is not the cause"
