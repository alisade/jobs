"""Hidden tests for platform/w5-c1: edge cases and failure paths."""
import json
import os
import pathlib
import sys
import textwrap

import pytest
import yaml

sys.path.insert(0, os.getcwd())
import gate  # noqa: E402

ROOT = pathlib.Path(os.getcwd())
POLICY = yaml.safe_load((ROOT / "config/policy.yaml").read_text())
ATTESTOR = POLICY["required_attestor"]
REPO = "us-docker.pkg.dev/tsl-artifacts-prod/riq/riq-api"
D1 = "sha256:" + "a" * 64
D2 = "sha256:" + "b" * 64
ATT = {"attestations": [{"resource_uri": f"{REPO}@{D1}", "digest": D1, "attestor": ATTESTOR}]}

GOOD_SC = {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True, "capabilities": {"drop": ["ALL"]}}
GOOD_RES = {"requests": {"cpu": "100m", "memory": "128Mi"}, "limits": {"memory": "128Mi"}}


def container(name="app", image=f"{REPO}@{D1}", probe=True, **extra):
    c = {"name": name, "image": image, "securityContext": dict(GOOD_SC), "resources": GOOD_RES}
    if probe:
        c["readinessProbe"] = {"httpGet": {"path": "/readyz", "port": 8080}}
    c.update(extra)
    return c


def sa(name="riq-api", ns="riq"):
    return {"apiVersion": "v1", "kind": "ServiceAccount", "metadata": {"name": name, "namespace": ns,
            "annotations": {"iam.gke.io/gcp-service-account": f"{name}@tsl-riq-prod.iam.gserviceaccount.com"}},
            "automountServiceAccountToken": False}


def pod_spec(containers, init=None, **extra):
    s = {"serviceAccountName": "riq-api", "securityContext": {"runAsNonRoot": True}, "containers": containers}
    if init:
        s["initContainers"] = init
    s.update(extra)
    return s


def deploy(spec, replicas=1, annotations=None, meta_annotations=None, name="riq-api"):
    tm = {"labels": {"app": name}}
    if annotations:
        tm["annotations"] = annotations
    m = {"name": name, "namespace": "riq"}
    if meta_annotations:
        m["annotations"] = meta_annotations
    return {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": m,
            "spec": {"replicas": replicas, "selector": {"matchLabels": {"app": name}}, "template": {"metadata": tm, "spec": spec}}}


def ev(docs, att=ATT):
    return gate.evaluate(docs, POLICY, att)


def rules(r, name=None):
    return sorted(v["rule"] for v in r["violations"] if name is None or v["name"] == name)


def test_clean_minimal_deployment():
    assert ev([sa(), deploy(pod_spec([container()]))])["violations"] == []


def test_list_kind_is_expanded():
    lst = {"apiVersion": "v1", "kind": "List", "items": [sa(), deploy(pod_spec([container(image="busybox:1.36")]))]}
    r = ev([*gate.load_documents(yaml.safe_dump(lst))])
    assert "IMG001" in rules(r, "riq-api")


def test_empty_docs_and_comments_are_skipped():
    text = "---\n# Source: riq-api/templates/empty.yaml\n---\n\n---\n" + yaml.safe_dump(sa()) + "---\n# only a comment\n"
    docs = gate.load_documents(text)
    assert [d["kind"] for d in docs] == ["ServiceAccount"]


def test_non_mapping_document_is_an_error():
    with pytest.raises(gate.GateError):
        gate.load_documents("- just\n- a list\n")


def test_cronjob_pod_template_is_checked():
    cj = {"apiVersion": "batch/v1", "kind": "CronJob", "metadata": {"name": "reindex", "namespace": "riq"},
          "spec": {"schedule": "0 3 * * *", "jobTemplate": {"spec": {"template": {"metadata": {},
                   "spec": pod_spec([container(name="job", probe=False, securityContext={"allowPrivilegeEscalation": True,
                                     "readOnlyRootFilesystem": True, "capabilities": {"drop": ["ALL"]}})], restartPolicy="OnFailure")}}}}}
    r = ev([sa(), cj])
    assert rules(r, "reindex") == ["SEC003"]


def test_init_containers_are_checked():
    init = [container(name="migrate", image="docker.io/library/flyway:10", probe=False, securityContext={})]
    r = ev([sa(), deploy(pod_spec([container()], init=init))])
    got = {v["rule"] for v in r["violations"] if v["container"] == "migrate"}
    assert {"IMG001", "IMG002", "SEC003", "SEC004", "SEC005"} <= got
    assert "PRB001" not in got, "init containers do not take readiness probes"


def test_tag_plus_digest_is_pinned_and_attested():
    r = ev([sa(), deploy(pod_spec([container(image=f"{REPO}:5.2.0@{D1}")]))])
    assert r["violations"] == []


def test_tag_only_is_not_pinned():
    r = ev([sa(), deploy(pod_spec([container(image=f"{REPO}:5.2.0")]))])
    assert rules(r) == ["IMG002"]


def test_malformed_digest_is_not_pinned():
    r = ev([sa(), deploy(pod_spec([container(image=f"{REPO}@sha256:deadbeef")]))])
    assert "IMG002" in rules(r)


def test_digest_without_attestation():
    r = ev([sa(), deploy(pod_spec([container(image=f"{REPO}@{D2}")]))])
    assert rules(r) == ["IMG003"]


def test_attestation_by_other_attestor_or_repo_does_not_count():
    att = {"attestations": [
        {"resource_uri": f"{REPO}@{D2}", "digest": D2, "attestor": "projects/tsl-security/attestors/qa-signoff"},
        {"resource_uri": f"us-docker.pkg.dev/tsl-artifacts-prod/riq/other@{D2}", "digest": D2, "attestor": ATTESTOR},
    ]}
    r = ev([sa(), deploy(pod_spec([container(image=f"{REPO}@{D2}")]))], att)
    assert rules(r) == ["IMG003"]


def test_break_glass_skips_only_attestation_and_is_recorded():
    d = deploy(pod_spec([container(image=f"{REPO}@{D2}"), container(name="sidecar", image="busybox:1.36")]),
               annotations={"alpha.image-policy.k8s.io/break-glass": "true"})
    r = ev([sa(), d])
    assert "IMG003" not in rules(r)
    assert {"IMG001", "IMG002"} <= set(rules(r)), "break-glass must not waive registry or digest rules"
    ex = r["exceptions"]
    assert len(ex) == 1 and ex[0]["rule"] == "IMG003" and ex[0]["name"] == "riq-api" and ex[0]["container"] == "app"


def test_break_glass_on_workload_metadata_does_not_count():
    d = deploy(pod_spec([container(image=f"{REPO}@{D2}")]), meta_annotations={"alpha.image-policy.k8s.io/break-glass": "true"})
    r = ev([sa(), d])
    assert rules(r) == ["IMG003"] and r["exceptions"] == []


def test_lookalike_registry_host_is_rejected():
    for img in (f"evil.example/us-docker.pkg.dev/tsl-artifacts-prod/riq/riq-api@{D1}",
                f"us-docker.pkg.dev/tsl-artifacts-dev/riq/riq-api@{D1}",
                f"gcr.io/tsl-artifacts-prod/riq-api@{D1}"):
        r = ev([sa(), deploy(pod_spec([container(image=img)]))], {"attestations": []})
        assert "IMG001" in rules(r), img


def test_other_region_artifact_registry_allowed():
    repo = "us-east4-docker.pkg.dev/tsl-artifacts-prod/riq/riq-api"
    att = {"attestations": [{"resource_uri": f"{repo}@{D1}", "digest": D1, "attestor": ATTESTOR}]}
    assert ev([sa(), deploy(pod_spec([container(image=f"{repo}@{D1}")]))], att)["violations"] == []


def test_run_as_non_root_inheritance():
    spec = pod_spec([container(), container(name="b", securityContext={**GOOD_SC, "runAsNonRoot": False})])
    r = ev([sa(), deploy(spec)])
    assert [(v["rule"], v["container"]) for v in r["violations"]] == [("SEC001", "b")]
    spec2 = pod_spec([container(securityContext={**GOOD_SC, "runAsNonRoot": True})], securityContext={})
    assert ev([sa(), deploy(spec2)])["violations"] == []


def test_privileged_and_memory_limit():
    c = container(securityContext={**GOOD_SC, "privileged": True}, resources={"requests": {"cpu": "1", "memory": "1Gi"}, "limits": {"cpu": "2"}})
    r = ev([sa(), deploy(pod_spec([c]))])
    assert rules(r) == ["RES001", "SEC002"]
    c2 = container(resources={"requests": {"cpu": "1", "memory": "1Gi"}, "limits": {"memory": "1Gi"}})
    assert ev([sa(), deploy(pod_spec([c2]))])["violations"] == [], "a CPU limit is not required"


def test_pdb_must_select_template_labels_in_same_namespace():
    d = deploy(pod_spec([container()]), replicas=3)
    wrong = {"apiVersion": "policy/v1", "kind": "PodDisruptionBudget", "metadata": {"name": "p", "namespace": "riq"},
             "spec": {"maxUnavailable": 1, "selector": {"matchLabels": {"app": "riq-api-canary"}}}}
    other_ns = {"apiVersion": "policy/v1", "kind": "PodDisruptionBudget", "metadata": {"name": "p", "namespace": "mdm"},
                "spec": {"maxUnavailable": 1, "selector": {"matchLabels": {"app": "riq-api"}}}}
    assert "PDB001" in rules(ev([sa(), d, wrong, other_ns]))
    right = {**wrong, "spec": {"maxUnavailable": 1, "selector": {"matchLabels": {"app": "riq-api"}}}}
    assert "PDB001" not in rules(ev([sa(), d, right]))
    assert "PDB001" not in rules(ev([sa(), deploy(pod_spec([container()]), replicas=1)]))


def test_workload_identity_rules():
    no_ann = {**sa(), "metadata": {"name": "riq-api", "namespace": "riq"}}
    assert "WI001" in rules(ev([no_ann, deploy(pod_spec([container()]))]))
    d_default = deploy(pod_spec([container()], serviceAccountName="default"))
    assert "WI001" in rules(ev([sa(), d_default]))
    assert "WI001" in rules(ev([deploy(pod_spec([container()]))])), "KSA missing from the render"
    mounted = {**sa(), "automountServiceAccountToken": True}
    assert [(v["rule"], v["kind"]) for v in ev([mounted, deploy(pod_spec([container()]))])["violations"]] == [("WI002", "ServiceAccount")]
    needs = {**sa(), "metadata": {**sa()["metadata"], "annotations": {**sa()["metadata"]["annotations"], "tessellate.example/needs-kube-api": "true"}}}
    needs.pop("automountServiceAccountToken")
    assert ev([needs, deploy(pod_spec([container()]))])["violations"] == []


def test_cli_parse_error_exits_2(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("kind: Deployment\n  metadata: [unclosed\n")
    assert gate.main(["--mode", "enforce", str(bad)]) == 2


def test_cli_enforce_clean_exits_0(tmp_path, capsys):
    f = tmp_path / "ok.yaml"
    f.write_text(yaml.safe_dump_all([sa(), deploy(pod_spec([container()]))]))
    att = tmp_path / "att.json"
    att.write_text(json.dumps(ATT))
    assert gate.main(["--mode", "enforce", "--attestations", str(att), str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["violations"] == [] and out["mode"] == "enforce"
