"""Write the w6-t1 evidence bundle (logs captured on ops-build-02, 2026-11-10). Do not edit."""

import sys
from pathlib import Path

FILES = {
    "README.txt": """Evidence bundle collected on ops-build-02 (Corvane Dunmore level 3 build box), 2026-11-10.
pip-before-CHG-4471.log   pip install, before the trusted-host change
pip-after-CHG-4471.log    pip install, after the change (works, with warnings)
uv-sync-ci.log            uv sync from the CI job (still failing)
uplink-client.log         the edge kit's uplink client (requests) at runtime
model-pull.log            model artefact download (requests)
s_client-*.txt            openssl s_client captures by plant IT
env.txt                   environment of the CI job
proxy-policy.txt          extract of the TLS inspection policy from the network team
CHG-4471.txt              the change record for the trusted-host workaround
""",
    "pip-before-CHG-4471.log": """$ pip install -v --no-cache-dir onnxruntime==1.20.1
Using pip 24.3.1 from /opt/edge-kit/.venv/lib/python3.12/site-packages/pip (python 3.12)
Looking in indexes: https://nexus.ops.corvane.internal/repository/pypi-proxy/simple
Created temporary directory: /tmp/pip-build-tracker-h2k1
Starting new HTTPS connection (1): proxy.corvane.internal:3128
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)'))': /repository/pypi-proxy/simple/onnxruntime/
WARNING: Retrying (Retry(total=3, ...)) after connection broken by 'SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)'))': /repository/pypi-proxy/simple/onnxruntime/
Could not fetch URL https://nexus.ops.corvane.internal/repository/pypi-proxy/simple/onnxruntime/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='nexus.ops.corvane.internal', port=443): Max retries exceeded with url: /repository/pypi-proxy/simple/onnxruntime/ (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)'))) - skipping
ERROR: Could not find a version that satisfies the requirement onnxruntime==1.20.1 (from versions: none)
""",
    "pip-after-CHG-4471.log": """$ pip install -v --no-cache-dir onnxruntime==1.20.1
Using pip 24.3.1 from /opt/edge-kit/.venv/lib/python3.12/site-packages/pip (python 3.12)
Looking in indexes: https://nexus.ops.corvane.internal/repository/pypi-proxy/simple
Starting new HTTPS connection (1): proxy.corvane.internal:3128
/opt/edge-kit/.venv/lib/python3.12/site-packages/pip/_vendor/urllib3/connectionpool.py:1103: InsecureRequestWarning: Unverified HTTPS request is being made to host 'nexus.ops.corvane.internal'. Adding certificate verification is strongly advised.
Collecting onnxruntime==1.20.1
  Downloading https://nexus.ops.corvane.internal/repository/pypi-proxy/packages/onnxruntime/1.20.1/onnxruntime-1.20.1-cp312-cp312-manylinux_2_27_x86_64.whl (13.3 MB)
Successfully installed onnxruntime-1.20.1
""",
    "uv-sync-ci.log": """$ uv sync --locked
DEBUG uv 0.9.2
DEBUG Using request timeout of 30s
DEBUG Found index `corvane-nexus`: https://nexus.ops.corvane.internal/repository/pypi-proxy/simple
DEBUG Using HTTPS proxy http://proxy.corvane.internal:3128
DEBUG Ignoring certificate verification for nexus.ops.corvane.internal (allow-insecure-host)
Resolved 41 packages in 2.31s
DEBUG Downloading https://models.tessellate-edge.example/kits/edge-kit-cli-2.3.0-py3-none-any.whl (direct URL dependency)
error: Failed to download `edge-kit-cli @ https://models.tessellate-edge.example/kits/edge-kit-cli-2.3.0-py3-none-any.whl`
  Caused by: Request failed after 3 retries
  Caused by: error sending request for url (https://models.tessellate-edge.example/kits/edge-kit-cli-2.3.0-py3-none-any.whl)
  Caused by: client error (Connect)
  Caused by: invalid peer certificate: UnknownIssuer
""",
    "uplink-client.log": """2026-11-10T08:02:11 INFO  uplink: sending 60 feature windows to https://telemetry.tessellate-edge.example/v1/ingest
2026-11-10T08:02:11 ERROR uplink: requests.exceptions.SSLError: HTTPSConnectionPool(host='telemetry.tessellate-edge.example', port=443): Max retries exceeded with url: /v1/ingest (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')))
2026-11-10T08:02:11 WARN  uplink: buffering 60 windows locally (buffer 18.2% full)
""",
    "model-pull.log": """2026-11-10T08:05:40 INFO  models: GET https://models.tessellate-edge.example/pump-health/v7/model.int8.onnx
2026-11-10T08:05:40 ERROR models: requests.exceptions.SSLError: HTTPSConnectionPool(host='models.tessellate-edge.example', port=443): Max retries exceeded (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')))
""",
    "s_client-telemetry-via-proxy.txt": """$ openssl s_client -proxy proxy.corvane.internal:3128 -connect telemetry.tessellate-edge.example:443 -servername telemetry.tessellate-edge.example -CAfile /opt/corvane/certs/corvane-root-g2.pem -showcerts </dev/null
CONNECTED(00000003)
depth=0 CN = telemetry.tessellate-edge.example
verify error:num=20:unable to get local issuer certificate
---
Certificate chain
 0 s:CN = telemetry.tessellate-edge.example
   i:C = US, O = Corvane Industrial, CN = Corvane Inspection Issuing CA 2
---
Server certificate
subject=CN = telemetry.tessellate-edge.example
issuer=C = US, O = Corvane Industrial, CN = Corvane Inspection Issuing CA 2
---
Verify return code: 20 (unable to get local issuer certificate)
""",
    "s_client-nexus-via-proxy.txt": """$ openssl s_client -proxy proxy.corvane.internal:3128 -connect nexus.ops.corvane.internal:443 -servername nexus.ops.corvane.internal -CAfile /opt/corvane/certs/corvane-root-g2.pem -showcerts </dev/null
CONNECTED(00000003)
depth=0 CN = nexus.ops.corvane.internal
verify error:num=20:unable to get local issuer certificate
---
Certificate chain
 0 s:CN = nexus.ops.corvane.internal
   i:C = US, O = Corvane Industrial, CN = Corvane Inspection Issuing CA 2
---
Verify return code: 20 (unable to get local issuer certificate)
""",
    "s_client-nexus-direct.txt": """$ openssl s_client -connect nexus.ops.corvane.internal:443 -servername nexus.ops.corvane.internal -CAfile /opt/corvane/certs/corvane-root-g2.pem -showcerts </dev/null
CONNECTED(00000003)
depth=2 C = US, O = Corvane Industrial, CN = Corvane Root CA G2
verify return:1
depth=1 C = US, O = Corvane Industrial, CN = Corvane Internal Issuing CA 1
verify return:1
depth=0 CN = nexus.ops.corvane.internal
verify return:1
---
Certificate chain
 0 s:CN = nexus.ops.corvane.internal
   i:C = US, O = Corvane Industrial, CN = Corvane Internal Issuing CA 1
 1 s:C = US, O = Corvane Industrial, CN = Corvane Internal Issuing CA 1
   i:C = US, O = Corvane Industrial, CN = Corvane Root CA G2
---
Verify return code: 0 (ok)
""",
    "s_client-models-via-proxy.txt": """$ openssl s_client -proxy proxy.corvane.internal:3128 -connect models.tessellate-edge.example:443 -servername models.tessellate-edge.example -CAfile /opt/corvane/certs/corvane-root-g2.pem -showcerts </dev/null
CONNECTED(00000003)
depth=1 C = US, O = Let's Encrypt, CN = R11
verify error:num=20:unable to get local issuer certificate
---
Certificate chain
 0 s:CN = models.tessellate-edge.example
   i:C = US, O = Let's Encrypt, CN = R11
 1 s:C = US, O = Let's Encrypt, CN = R11
   i:C = US, O = Internet Security Research Group, CN = ISRG Root X1
---
Verify return code: 20 (unable to get local issuer certificate)
""",
    "env.txt": """HTTPS_PROXY=http://proxy.corvane.internal:3128
HTTP_PROXY=http://proxy.corvane.internal:3128
NO_PROXY=localhost,127.0.0.1
REQUESTS_CA_BUNDLE=/opt/corvane/certs/corvane-root-g2.pem
SSL_CERT_FILE=/opt/corvane/certs/corvane-root-g2.pem
CURL_CA_BUNDLE=/opt/corvane/certs/corvane-root-g2.pem
PIP_TRUSTED_HOST=pypi.org files.pythonhosted.org nexus.ops.corvane.internal
""",
    "proxy-policy.txt": """TLS inspection policy (proxy.corvane.internal), extract, network team, rev 14
- All HTTPS through the proxy is inspected: the proxy terminates TLS and re-signs with a leaf issued by
  "Corvane Inspection Issuing CA 2" (chains to "Corvane Root CA G2"). The proxy sends the leaf only.
- Not inspected (tunnelled as-is, original certificate chain): hosts on the pinned list.
  Pinned list: models.tessellate-edge.example (vendor artefact signing requirement, RITM-20931)
- Internal hosts (*.corvane.internal) are reachable directly from level 3 and must not be sent to the
  proxy; the proxy inspects them like any other host when they are.
- The corporate PKI root and both issuing CAs are published at http://pki.corvane.internal/ (PEM).
""",
    "CHG-4471.txt": """CHG-4471  Standard change  2026-11-07  Implementer: J. Ortiz
Summary: pip install failing on ops-build-02 with SSL errors. Added PIP_TRUSTED_HOST for pypi.org,
files.pythonhosted.org and nexus.ops.corvane.internal; added allow-insecure-host to uv.toml.
Result: pip works. uv still fails on the edge-kit-cli download. Uplink client still failing.
Security review 2026-11-09 (M. Lindqvist): trusted-host and allow-insecure-host disable certificate
verification and are not acceptable on a build host. Revert required by 2026-11-14.
""",
}

if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
    out.mkdir(parents=True, exist_ok=True)
    for name, text in FILES.items():
        (out / name).write_text(text)
    print(f"wrote {len(FILES)} files to {out}/")
