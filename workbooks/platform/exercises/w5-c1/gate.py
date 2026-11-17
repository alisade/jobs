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
    # TODO: helm template output has empty documents (a lone "---" or comment-only docs) and
    # `kubectl get -o yaml` style input arrives as kind: List with items. Handle both; raise
    # GateError for a document that is not a mapping or has no kind.
    return [d for d in raw]


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
    # TODO: support every kind in WORKLOAD_KINDS (a CronJob nests its template one level deeper,
    # a bare Pod has no template at all).
    if obj.get("kind") == "Deployment":
        return (obj.get("spec") or {}).get("template")
    return None


def all_containers(pod_spec: dict) -> list[tuple[str, dict]]:
    # TODO: init containers and ephemeral containers run code too.
    return [("containers", c) for c in pod_spec.get("containers") or []]


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
    # First draft from the PLAT-1201 spike. Review it before you trust it.
    for rule in policy.get("allowed_registries", []):
        if fnmatch.fnmatchcase(img["repo"], rule["host"] + "/" + rule.get("path_prefix", "") + "*"):
            return True
    return False


def is_digest(d: str | None) -> bool:
    # TODO: a real sha256 digest, not just "something after @".
    return bool(d)


def attested(img: dict, attestations: dict, attestor: str) -> bool:
    # TODO: an attestation counts only if it is by the required attestor, for this digest and
    # for this repository (resource_uri without the @digest equals the image repo).
    raise NotImplementedError("attested")


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

    # TODO WI002 for ServiceAccount objects (see README).

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
            # TODO IMG003: digest must be attested by policy["required_attestor"]; a pod-template
            #   break-glass annotation turns the violation into an audited entry in `exceptions`
            #   (and skips ONLY this rule).
            # TODO SEC001-SEC005: runAsNonRoot (pod level is inherited, container level wins),
            #   privileged, allowPrivilegeEscalation, readOnlyRootFilesystem, capabilities drop ALL.
            # TODO RES001: requests.cpu, requests.memory, limits.memory.
            # TODO PRB001: readinessProbe on Deployment app containers.

        # TODO WI001 / WI002 for the pod: dedicated KSA from the render with a valid
        #   iam.gke.io/gcp-service-account annotation; pod-level automountServiceAccountToken: true.
        # TODO PDB001: Deployment/StatefulSet with replicas > 1 needs a PDB in the same namespace whose
        #   matchLabels select the pod template labels.

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
