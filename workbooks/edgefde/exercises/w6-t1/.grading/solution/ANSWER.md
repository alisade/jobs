# ANSWER: edgefde/w6-t1 pip and uv fail behind a TLS-inspecting proxy

## Approach

Read the proxy policy first, then compared the three s_client captures: nexus direct verifies with
the root alone, nexus via the proxy and telemetry via the proxy fail with code 20 and a one-cert
chain, models via the proxy shows a public Let's Encrypt chain.

## Root cause

The proxy terminates and re-signs every proxied HTTPS connection with a leaf from "Corvane Inspection
Issuing CA 2" and sends only the leaf:

```text
 0 s:CN = telemetry.tessellate-edge.example
   i:C = US, O = Corvane Industrial, CN = Corvane Inspection Issuing CA 2
Verify return code: 20 (unable to get local issuer certificate)
```

Every client trusts only `corvane-root-g2.pem`, so it cannot build the chain: that is the uplink
client error and pip's error before CHG-4471. Two things made it worse: `NO_PROXY` lacks
`.corvane.internal`, so nexus is sent through the proxy and inspected (direct it verifies fine), and
the root-only bundle has no public roots, so the pinned, uninspected model host (Let's Encrypt R11 ->
ISRG Root X1) fails for uv (`UnknownIssuer`) and requests.

CHG-4471 only turned verification off for pip (and for nexus in uv); requests ignores both settings
and the model host was never covered, which is why only pip "worked".

## Fix

`build-ca-bundle.sh` now concatenates public roots, Corvane Root CA G2, Inspection Issuing CA 2 and
Internal Issuing CA 1 into `/opt/corvane/certs/ca-bundle.pem`, each block on its own lines. All
clients point at it (`REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE`, `PIP_CERT`, pip `cert`);
`NO_PROXY=localhost,127.0.0.1,.corvane.internal`; trusted-host and allow-insecure-host removed.
Verification for plant IT: `openssl s_client` with `-CAfile /opt/corvane/certs/ca-bundle.pem` via the
proxy to telemetry and models and direct to nexus (all code 0), `curl -v`, `pip download`,
`uv sync --locked`, one requests call; then confirm CHG-4471 is reverted.

## Trade-offs / what I would do in production

Rebuild the bundle from the OS trust store on every CA rotation (a scheduled job, alert on expiry).
Venvs that vendor certifi ignore the OS store, so the env variables matter. This becomes a section of
the site readiness checklist that ships with the handoff pack.
