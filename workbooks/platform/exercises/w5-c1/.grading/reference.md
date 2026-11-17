# Reference: platform/w5-c1

The reference implementation is `.grading/solution/gate.py`. Key points:

- `load_documents` walks `yaml.safe_load_all`, drops `None` (empty or comment-only documents), expands
  `kind: List` (and `*List` with items) iteratively, and raises `GateError` for non-mapping documents.
- One `pod_template()` returns `{metadata, spec}` for every workload kind (CronJob at
  `spec.jobTemplate.spec.template`, Pod is its own template); `all_containers()` yields init, app and
  ephemeral containers with their field name, so per-field exceptions (RES001 for ephemeral, PRB001 only
  for app containers) are easy.
- `parse_image` splits host, path, tag and digest: the first component is a host only if it has a dot,
  a colon or is localhost (otherwise docker.io and `library/` for single names). The spike's
  `fnmatch` over the whole reference let `evil.example/us-docker.pkg.dev/tsl-artifacts-prod/...` pass,
  because `*` in fnmatch also matches `/`.
- `is_digest` requires `sha256:` plus 64 lowercase hex characters.
- `attested` matches attestor, digest and repository (`resource_uri` before `@`).
- Break-glass is read from the pod template annotations only and converts IMG003 into an exception
  record. Registry and digest rules still apply: a break-glass deploy is still traceable to a digest.
- CLI: dry-run exits 0, enforce exits 1 on any violation, 2 on parse or read errors.

Shipped render: riq-reindex uses `busybox:1.36` (docker.io, a tag) - IMG001 + IMG002. rdm-worker's
digest is attested by `qa-signoff`, not by `prod-build-verified` - IMG003 (it was built from an rc tag
outside the prod pipeline); it has 3 replicas and no PDB - PDB001; its KSA does not disable token
automount - WI002.

Production framing: the CI gate is feedback, Binary Authorization is enforcement (CI can be bypassed by
kubectl or a hotfix pipeline). Roll out in dry-run, read the would-deny audit log entries, then enforce
per cluster; exempt system namespaces with the documented allow-list; alert on every break-glass deploy.
