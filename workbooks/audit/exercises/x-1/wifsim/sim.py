"""Simulate the keyless call path Azure Function -> Google STS -> IAM Credentials -> Gemini.

Complete and faithful for this exercise; the bug is in config/, not here. The rules follow the
Google Cloud docs for Workload Identity Federation with other clouds (Azure):

  1. Subject token: the Function's managed identity asks Azure IMDS for an Entra token with
     resource=<credential_source.url resource>. The token's aud is that resource.
  2. STS exchange (sts.googleapis.com/v1/token): the credential config "audience" must be the full
     provider resource name; the token issuer must equal the provider's issuer_uri; the token aud
     must be in allowed_audiences; the attribute_condition must hold; attribute_mapping produces
     google.subject (and optional attribute.*). The federated principal is
     principal://iam.googleapis.com/projects/<number>/locations/global/workloadIdentityPools/<pool>/subject/<google.subject>
  3. Impersonation (iamcredentials generateAccessToken on the service account): the service
     account's IAM policy must grant roles/iam.workloadIdentityUser to that principal, or to a
     principalSet that contains it.
  4. Gemini call: the service account needs roles/aiplatform.user on the project.

Usage:  python -m wifsim.sim [--claims incident/token-claims.json] [--config config]
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Result:
    ok: bool
    stage: str
    principal: str | None = None
    lines: list[str] = field(default_factory=list)


def _load(config_dir: Path, name: str) -> dict:
    return json.loads((config_dir / name).read_text())


def _eval_condition(cond: str, claims: dict) -> bool:
    """Supports the CEL subset used here: assertion.<claim> == '<value>' joined by &&."""
    if not cond:
        return True
    for clause in cond.split("&&"):
        m = re.fullmatch(r"\s*assertion\.(\w+)\s*==\s*'([^']*)'\s*", clause)
        if not m:
            raise ValueError(f"unsupported attribute_condition clause: {clause!r}")
        if str(claims.get(m.group(1))) != m.group(2):
            return False
    return True


def _map(mapping: dict, claims: dict) -> dict:
    out = {}
    for target, expr in mapping.items():
        m = re.fullmatch(r"assertion\.(\w+)", expr.strip())
        if not m:
            raise ValueError(f"unsupported mapping expression: {expr!r}")
        if m.group(1) in claims:
            out[target] = str(claims[m.group(1)])
    return out


def _member_matches(member: str, pool_prefix: str, subject: str, attrs: dict) -> bool:
    if member == f"principal://{pool_prefix}/subject/{subject}":
        return True
    if member == f"principalSet://{pool_prefix}/*":
        return True
    m = re.fullmatch(re.escape(f"principalSet://{pool_prefix}/attribute.") + r"(\w+)/(.+)", member)
    if m and attrs.get(f"attribute.{m.group(1)}") == m.group(2):
        return True
    return member in ("allUsers", "allAuthenticatedUsers")


def simulate(claims: dict, config_dir: str | Path = ROOT / "config") -> Result:
    cfg_dir = Path(config_dir)
    cred = _load(cfg_dir, "credential-config.json")
    prov = _load(cfg_dir, "wif-provider.json")
    sa_policy = _load(cfg_dir, "sa-iam-policy.json")
    project_policy = _load(cfg_dir, "project-iam-policy.json")
    r = Result(ok=False, stage="subject_token")

    if cred.get("type") != "external_account":
        r.lines.append(f"google.auth: credential type {cred.get('type')!r} is not external_account; keyless federation not in use")
        return r
    url = cred.get("credential_source", {}).get("url", "")
    resource = parse_qs(urlparse(url).query).get("resource", [""])[0]
    if claims.get("aud") != resource:
        r.lines.append(f"IMDS: token aud {claims.get('aud')!r} does not match requested resource {resource!r}")
        return r
    r.lines.append(f"IMDS: managed identity token issued, aud={claims['aud']} sub={claims.get('sub')} appid={claims.get('appid')}")

    r.stage = "sts_exchange"
    expected = (f"//iam.googleapis.com/projects/{prov['project_number']}/locations/global/"
                f"workloadIdentityPools/{prov['pool_id']}/providers/{prov['provider_id']}")
    if cred.get("audience") != expected:
        r.lines.append(f"STS 400 invalid_target: The target service indicated by the \"audience\" parameter is invalid ({cred.get('audience')})")
        return r
    if claims.get("iss") != prov["oidc"]["issuer_uri"]:
        r.lines.append(f"STS 400 invalid_grant: The issuer in ID Token {claims.get('iss')} does not match the expected ones: {prov['oidc']['issuer_uri']}")
        return r
    if claims.get("aud") not in prov["oidc"].get("allowed_audiences", []):
        r.lines.append(f"STS 400 invalid_grant: The audience in ID Token [{claims.get('aud')}] does not match the expected audience.")
        return r
    if not _eval_condition(prov.get("attribute_condition", ""), claims):
        r.lines.append("STS 400 unauthorized_client: The given credential is rejected by the attribute condition.")
        return r
    attrs = _map(prov.get("attribute_mapping", {}), claims)
    subject = attrs.get("google.subject")
    if not subject:
        r.lines.append("STS 400 invalid_grant: The mapped attribute 'google.subject' must not be empty.")
        return r
    pool_prefix = (f"iam.googleapis.com/projects/{prov['project_number']}/locations/global/"
                   f"workloadIdentityPools/{prov['pool_id']}")
    r.principal = f"principal://{pool_prefix}/subject/{subject}"
    r.lines.append(f"STS 200: federated token issued for {r.principal}")

    r.stage = "impersonation"
    sa = re.search(r"serviceAccounts/([^:]+):generateAccessToken", cred.get("service_account_impersonation_url", ""))
    sa_email = sa.group(1) if sa else "?"
    granted = any(
        b["role"] == "roles/iam.workloadIdentityUser" and any(_member_matches(m, pool_prefix, subject, attrs) for m in b["members"])
        for b in sa_policy.get("bindings", [])
    )
    if not granted:
        r.lines.append(f"iamcredentials 403 PERMISSION_DENIED: Permission 'iam.serviceAccounts.getAccessToken' denied on resource "
                       f"(or it may not exist). principal={r.principal} serviceAccount={sa_email}")
        return r
    r.lines.append(f"iamcredentials 200: access token issued for {sa_email}")

    r.stage = "gemini"
    member = f"serviceAccount:{sa_email}"
    if not any(b["role"] in ("roles/aiplatform.user", "roles/owner", "roles/editor") and member in b["members"]
               for b in project_policy.get("bindings", [])):
        r.lines.append(f"aiplatform 403 PERMISSION_DENIED: Permission 'aiplatform.endpoints.predict' denied for {member}")
        return r
    r.lines.append(f"aiplatform 200: generateContent gemini-3.8-flash as {sa_email}")
    r.ok, r.stage = True, "done"
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=str(ROOT / "incident" / "token-claims.json"))
    ap.add_argument("--config", default=str(ROOT / "config"))
    a = ap.parse_args()
    res = simulate(json.loads(Path(a.claims).read_text()), a.config)
    print("\n".join(res.lines))
    print(f"RESULT {'OK' if res.ok else 'FAILED at ' + res.stage}")
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
