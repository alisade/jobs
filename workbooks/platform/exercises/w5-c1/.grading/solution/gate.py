#!/usr/bin/env python3
"""Admission gate for Helm-rendered manifests (Tessellate platform CI).

Runs in CI after `helm template` and before ArgoCD syncs a chart to prod-blue / prod-green.
It is the pre-admission twin of Binary Authorization plus the GKE hardening baseline:
registry allow-list, digest pinning, attestation by the required attestor, pod hardening,
resources, probes, PDBs and Workload Identity Federation for GKE.

Usage:
  python gate.py --mode dry-run|enforce [--policy config/policy.yaml]
                 [--attestations config/attestations.json] FILE_OR_DIR [...]
Exit codes: 0 ok (or dry-run), 1 violations in enforce mode, 2 usage or parse error.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import sys
from dataclasses import asdict, dataclass

import yaml

BREAK_GLASS = "alpha.image-policy.k8s.io/break-glass"
WI_ANNOTATION = "iam.gke.io/gcp-service-account"
NEEDS_API = "tessellate.example/needs-kube-api"

WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob", "Pod"}

DEFAULT_POLICY = {
    "allowed_registries": [
        {"host": "*-docker.pkg.dev", "path_prefix": "tsl-artifacts-prod/"},
    ],
    "required_attestor": "projects/tsl-security/attestors/prod-build-verified",
    "default_namespace": "default",
}


class GateError(Exception):
    """Input could not be parsed; the CLI exits 2."""


@dataclass
class Finding:
    rule: str
    kind: str
    name: str
    namespace: str
    container: str
    message: str


# ---------------------------------------------------------------- loading
def load_documents(text: str) -> list[dict]:
    """Parse multi-document YAML; skip empty documents, expand kind: List."""
    try:
        raw = list(yaml.safe_load_all(text))
    except yaml.YAMLError as e:
        raise GateError(f"invalid YAML: {e}") from e
    out: list[dict] = []
    stack = list(reversed(raw))
    while stack:
        d = stack.pop()
        if d is None:
            continue
        if not isinstance(d, dict):
            raise GateError(f"document is not a mapping: {type(d).__name__}")
        if d.get("kind") == "List" or (d.get("kind", "").endswith("List") and "items" in d):
            stack.extend(reversed(d.get("items") or []))
            continue
        if "kind" not in d:
            raise GateError("document without kind")
        out.append(d)
    return out


def load_paths(paths: list[str]) -> list[dict]:
    docs: list[dict] = []
    for p in paths:
        path = pathlib.Path(p)
        files = sorted(path.rglob("*.y*ml")) if path.is_dir() else [path]
        for f in files:
            try:
                docs.extend(load_documents(f.read_text()))
            except OSError as e:
                raise GateError(f"cannot read {f}: {e}") from e
    return docs


# ---------------------------------------------------------------- helpers
def meta(obj: dict) -> dict:
    return obj.get("metadata") or {}


def ns_of(obj: dict, policy: dict) -> str:
    return meta(obj).get("namespace") or policy.get("default_namespace", "default")


def pod_template(obj: dict) -> dict | None:
    """Return the pod template ({metadata, spec}) of a workload, or None."""
    kind = obj.get("kind")
    spec = obj.get("spec") or {}
    if kind == "Pod":
        return {"metadata": meta(obj), "spec": spec}
    if kind == "CronJob":
        return ((spec.get("jobTemplate") or {}).get("spec") or {}).get("template")
    if kind in WORKLOAD_KINDS:
        return spec.get("template")
    return None


def all_containers(pod_spec: dict) -> list[tuple[str, dict]]:
    out = []
    for field in ("initContainers", "containers", "ephemeralContainers"):
        for c in pod_spec.get(field) or []:
            out.append((field, c))
    return out


def parse_image(ref: str) -> dict:
    """Split an image reference into host, path, tag, digest."""
    digest = None
    if "@" in ref:
        ref, digest = ref.split("@", 1)
    first, _, rest = ref.partition("/")
    if rest and ("." in first or ":" in first or first == "localhost"):
        host, path = first, rest
    else:
        host, path = "docker.io", ref if "/" in ref else "library/" + ref
    tag = None
    last = path.rsplit("/", 1)[-1]
    if ":" in last:
        path, tag = path.rsplit(":", 1)
    return {"host": host, "path": path, "tag": tag, "digest": digest, "repo": f"{host}/{path}"}


def registry_allowed(img: dict, policy: dict) -> bool:
    for rule in policy.get("allowed_registries", []):
        if fnmatch.fnmatchcase(img["host"], rule["host"]) and "/" not in img["host"] \
                and img["path"].startswith(rule.get("path_prefix", "")):
            return True
    return False


def is_digest(d: str | None) -> bool:
    if not d or not d.startswith("sha256:"):
        return False
    h = d[len("sha256:"):]
    return len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def attested(img: dict, attestations: dict, attestor: str) -> bool:
    for a in attestations.get("attestations", []):
        if a.get("attestor") == attestor and a.get("digest") == img["digest"] \
                and a.get("resource_uri", "").split("@")[0] == img["repo"]:
            return True
    return False


def selector_matches(selector: dict, labels: dict) -> bool:
    ml = (selector or {}).get("matchLabels") or {}
    if not ml:
        return False
    return all(labels.get(k) == v for k, v in ml.items())


# ---------------------------------------------------------------- rules
def evaluate(docs: list[dict], policy: dict | None = None, attestations: dict | None = None) -> dict:
    policy = {**DEFAULT_POLICY, **(policy or {})}
    attestations = attestations or {"attestations": []}
    attestor = policy["required_attestor"]
    findings: list[Finding] = []
    exceptions: list[dict] = []

    sas = {(ns_of(d, policy), meta(d).get("name")): d for d in docs if d.get("kind") == "ServiceAccount"}
    pdbs = [d for d in docs if d.get("kind") == "PodDisruptionBudget"]

    def add(rule, obj, container, msg):
        findings.append(Finding(rule, obj.get("kind", ""), meta(obj).get("name", ""), ns_of(obj, policy), container, msg))

    for sa in sas.values():
        ann = meta(sa).get("annotations") or {}
        if sa.get("automountServiceAccountToken") is not False and str(ann.get(NEEDS_API, "")).lower() != "true":
            add("WI002", sa, "", "automountServiceAccountToken must be false unless the KSA needs the Kubernetes API")

    for obj in docs:
        tpl = pod_template(obj)
        if tpl is None:
            continue
        pmeta = tpl.get("metadata") or {}
        pspec = tpl.get("spec") or {}
        ann = pmeta.get("annotations") or {}
        break_glass = str(ann.get(BREAK_GLASS, "")).lower() == "true"
        pod_sc = pspec.get("securityContext") or {}

        for field, c in all_containers(pspec):
            cname = c.get("name", "")
            img = parse_image(c.get("image", ""))
            if not registry_allowed(img, policy):
                add("IMG001", obj, cname, f"image {c.get('image')} is not from an allowed Artifact Registry repository")
            if not is_digest(img["digest"]):
                add("IMG002", obj, cname, f"image {c.get('image')} is not pinned by @sha256 digest")
            elif not attested(img, attestations, attestor):
                if break_glass:
                    exceptions.append({"rule": "IMG003", "kind": obj.get("kind"), "name": meta(obj).get("name"),
                                       "namespace": ns_of(obj, policy), "container": cname,
                                       "image": c.get("image"), "reason": "break-glass annotation on pod template (audited)"})
                else:
                    add("IMG003", obj, cname, f"digest {img['digest']} has no attestation by {attestor}")

            sc = c.get("securityContext") or {}
            run_non_root = sc.get("runAsNonRoot", pod_sc.get("runAsNonRoot"))
            if run_non_root is not True:
                add("SEC001", obj, cname, "runAsNonRoot must be true (pod or container securityContext)")
            if sc.get("privileged") is True:
                add("SEC002", obj, cname, "privileged containers are not allowed")
            if sc.get("allowPrivilegeEscalation") is not False:
                add("SEC003", obj, cname, "allowPrivilegeEscalation must be false")
            if sc.get("readOnlyRootFilesystem") is not True:
                add("SEC004", obj, cname, "readOnlyRootFilesystem must be true")
            drops = [str(x).upper() for x in ((sc.get("capabilities") or {}).get("drop") or [])]
            if "ALL" not in drops:
                add("SEC005", obj, cname, "capabilities.drop must include ALL")
            if field != "ephemeralContainers":
                res = c.get("resources") or {}
                req = res.get("requests") or {}
                lim = res.get("limits") or {}
                if "cpu" not in req or "memory" not in req or "memory" not in lim:
                    add("RES001", obj, cname, "requests.cpu, requests.memory and limits.memory are required")
            if obj.get("kind") == "Deployment" and field == "containers" and not c.get("readinessProbe"):
                add("PRB001", obj, cname, "Deployment containers need a readinessProbe")

        if pspec.get("automountServiceAccountToken") is True:
            add("WI002", obj, "", "pod sets automountServiceAccountToken: true")
        ksa = pspec.get("serviceAccountName") or pspec.get("serviceAccount") or "default"
        if ksa == "default":
            add("WI001", obj, "", "workload runs as the default KSA; use a dedicated KSA bound with Workload Identity")
        else:
            sa = sas.get((ns_of(obj, policy), ksa))
            gsa_email = ((meta(sa).get("annotations") or {}).get(WI_ANNOTATION, "") if sa else "")
            if not sa:
                add("WI001", obj, "", f"KSA {ksa} is not in the render; cannot verify its Workload Identity binding")
            elif not (gsa_email.endswith(".iam.gserviceaccount.com") and "@" in gsa_email):
                add("WI001", obj, "", f"KSA {ksa} lacks a valid {WI_ANNOTATION} annotation")

        if obj.get("kind") in ("Deployment", "StatefulSet"):
            replicas = (obj.get("spec") or {}).get("replicas", 1)
            if isinstance(replicas, int) and replicas > 1:
                labels = pmeta.get("labels") or {}
                if not any(ns_of(p, policy) == ns_of(obj, policy) and selector_matches((p.get("spec") or {}).get("selector"), labels) for p in pdbs):
                    add("PDB001", obj, "", f"{replicas} replicas but no PodDisruptionBudget selects the pod template labels")

    return {
        "violations": [asdict(f) for f in findings],
        "exceptions": exceptions,
        "summary": {"documents": len(docs), "violations": len(findings), "exceptions": len(exceptions)},
    }


# ---------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("dry-run", "enforce"), default="dry-run")
    ap.add_argument("--policy")
    ap.add_argument("--attestations")
    ap.add_argument("paths", nargs="+")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        policy = yaml.safe_load(pathlib.Path(args.policy).read_text()) if args.policy else None
        att = json.loads(pathlib.Path(args.attestations).read_text()) if args.attestations else None
        docs = load_paths(args.paths)
    except (GateError, OSError, json.JSONDecodeError, yaml.YAMLError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    result = evaluate(docs, policy, att)
    result["mode"] = args.mode
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.mode == "enforce" and result["violations"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
