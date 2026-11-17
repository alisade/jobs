"""Write incident/: the decoded Entra token, the Function app log and the GCP-side audit log lines,
generated from the current config/ through the simulator. `make setup` runs this."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .sim import ROOT, simulate

MI = {"name": "id-controlpilot-func", "type": "Microsoft.ManagedIdentity/userAssignedIdentities",
      "clientId": "9a41e0b5-2c7d-4f38-8e19-d5b6a3c0f271", "principalId": "3f9d2c71-8a4b-4e6f-b1d2-6c7e9a0f5b84",
      "tenantId": "7c1e4b2a-5d3f-4e81-9a6c-2b0d8f4e1a37"}


def main(out_dir: str = "incident") -> int:
    out = ROOT / out_dir
    out.mkdir(exist_ok=True)
    claims = json.loads((ROOT / "wifsim" / "sample_claims.json").read_text())
    (out / "token-claims.json").write_text(json.dumps(claims, indent=2) + "\n")
    (out / "managed-identity.json").write_text(
        "// az identity show -g rg-controlpilot-prod -n id-controlpilot-func\n" + json.dumps(MI, indent=2) + "\n")
    res = simulate(claims)
    log = ["2026-11-10T02:00:04.118Z [Information] Executing 'Functions.cm03_nightly' (Reason='Timer fired', Id=5f1c0e2a)",
           "2026-11-10T02:00:04.212Z [Information] google.auth: loading external_account credentials from GOOGLE_APPLICATION_CREDENTIALS=/home/site/wwwroot/gcp-wif.json"]
    log += [f"2026-11-10T02:00:04.{300 + 40 * i:03d}Z [{'Error' if not res.ok and i == len(res.lines) - 1 else 'Information'}] {line}"
            for i, line in enumerate(res.lines)]
    if not res.ok:
        log.append("2026-11-10T02:00:04.900Z [Error] google.auth.exceptions.RefreshError: ('Unable to acquire impersonated credentials', "
                   "'{\"error\": {\"code\": 403, \"message\": \"Permission \\'iam.serviceAccounts.getAccessToken\\' denied on resource (or it may not exist).\", \"status\": \"PERMISSION_DENIED\"}}')"
                   if res.stage == "impersonation" else f"2026-11-10T02:00:04.900Z [Error] call failed at {res.stage}")
        log.append("2026-11-10T02:00:04.902Z [Error] Executed 'Functions.cm03_nightly' (Failed, Id=5f1c0e2a, Duration=784ms)")
    else:
        log.append("2026-11-10T02:00:05.410Z [Information] Executed 'Functions.cm03_nightly' (Succeeded, Id=5f1c0e2a)")
    (out / "function-app.log").write_text("\n".join(log) + "\n")
    gcp = ["# Cloud Audit Logs (Data Access), project mfh-controlpilot-prod, 2026-11-10 02:00 UTC",
           "sts.googleapis.com  google.identity.sts.v1.SecurityTokenService.ExchangeToken  status=OK"
           f"  principal={res.principal}" if res.principal else "sts.googleapis.com ExchangeToken status=FAILED"]
    if res.stage in ("impersonation",) and not res.ok:
        gcp.append("iamcredentials.googleapis.com  GenerateAccessToken  status=PERMISSION_DENIED(7)"
                   f"  authenticationInfo.principalSubject={res.principal}"
                   "  resource=projects/-/serviceAccounts/controlpilot-gemini@mfh-controlpilot-prod.iam.gserviceaccount.com")
    (out / "gcp-audit.log").write_text("\n".join(gcp) + "\n")
    print("\n".join(res.lines))
    print(f"RESULT {'OK' if res.ok else 'FAILED at ' + res.stage}  (bundle in {out_dir}/)")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
