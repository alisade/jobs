# Reference: edgefde/w6-t1

Primary cause: the proxy inspects all proxied HTTPS and re-signs it with a leaf issued by "Corvane
Inspection Issuing CA 2", sending the leaf only (`s_client-telemetry-via-proxy.txt`: chain depth 0
only, verify return code 20). Every client was given `corvane-root-g2.pem` alone, so no client can
build leaf -> issuing CA 2 -> root. That is the uplink client's error and pip's original error.

Contributing:
- `NO_PROXY=localhost,127.0.0.1` sends `nexus.ops.corvane.internal` through the proxy, which then
  inspects it (`s_client-nexus-via-proxy.txt` fails; `s_client-nexus-direct.txt` verifies OK with the
  root alone because nexus sends its own intermediate). Add `.corvane.internal`.
- `models.tessellate-edge.example` is on the proxy's pinned (not inspected) list, so it presents its
  public chain (Let's Encrypt R11 -> ISRG Root X1). A root-only corporate bundle has no public roots:
  uv reports `UnknownIssuer` and requests `unable to get local issuer certificate`.

Why CHG-4471 "worked": `PIP_TRUSTED_HOST` disables verification for those hosts in pip only. uv's
`allow-insecure-host` covered nexus but not the model host; requests ignores both. It is a security
finding and must be reverted.

Fix (`.grading/solution/site/`): bundle = public roots + Corvane Root CA G2 + Inspection Issuing CA 2
(+ Internal Issuing CA 1), each block on its own lines; `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`,
`CURL_CA_BUNDLE`, `PIP_CERT` and pip `cert` all point at `/opt/corvane/certs/ca-bundle.pem`;
`NO_PROXY=localhost,127.0.0.1,.corvane.internal`; no bypasses.

Verification: `openssl s_client -proxy proxy.corvane.internal:3128 -connect telemetry...:443 -CAfile
/opt/corvane/certs/ca-bundle.pem` gives code 0; same for models; direct to nexus; `curl -v`,
`pip download onnxruntime==1.20.1`, `uv sync --locked`, `python -c "import requests;
requests.get('https://telemetry.tessellate-edge.example/health')"`; then revert CHG-4471 and rerun.
