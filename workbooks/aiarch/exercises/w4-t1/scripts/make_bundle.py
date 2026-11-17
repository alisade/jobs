"""Generate incident evidence for aiarch/w4-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""SEC-3107  High  Contractor manager approved a payments access request through the agent
Opened 2026-11-13 08:40 by security operations (A. Haddad)

AR-1187 (jdiaz, ledger-admin, team payments) was approved at 2026-11-12 19:22 by
vk-ext-0042, a contractor manager from the partner IdP who manages the claims vendor team.
The approval went through the Lighthouse agent's approve_access_request tool on the gateway.

Policy engine history: LOG_ONLY from 2026-11-03, switched to ENFORCE 2026-11-12 18:00
(CHG-8820). During LOG_ONLY the team read the decision log and saw no unexpected ALLOW for
employees and workforce managers.

On-call notes:
- 08:55 (R. Patel) Approval happened one hour after the switch to ENFORCE, so ENFORCE is not
  actually enforcing. Proposing to roll back to LOG_ONLY and open a support case.
- 09:05 (R. Patel) The forbid-cross-team policy is right there in the file. Cedar must be
  evaluating permits first.
""")
dec = [
 {"ts": "2026-11-12T17:51:09Z", "mode": "LOG_ONLY", "principal": "User::\"lwong\"", "action": "approve_access_request",
  "input": {"request_id": "AR-1180", "team": "claims", "requester": "mchen"}, "decision": "DENY", "determining": ["policy2"], "errors": []},
 {"ts": "2026-11-12T18:03:44Z", "mode": "ENFORCE", "principal": "User::\"lwong\"", "action": "approve_access_request",
  "input": {"request_id": "AR-1183", "team": "payments", "requester": "tkhan"}, "decision": "ALLOW", "determining": ["policy1"], "errors": []},
 {"ts": "2026-11-12T19:22:17Z", "mode": "ENFORCE", "principal": "User::\"vk-ext-0042\"", "action": "approve_access_request",
  "input": {"request_id": "AR-1187", "team": "payments", "requester": "jdiaz"}, "decision": "ALLOW", "determining": ["policy1"],
  "errors": ["error while evaluating policy `policy2`: `User::\"vk-ext-0042\"` does not have the attribute `team`"]},
 {"ts": "2026-11-07T10:12:00Z", "mode": "LOG_ONLY", "principal": "User::\"vk-ext-0042\"", "action": "approve_access_request",
  "input": {"request_id": "AR-1102", "team": "claims", "requester": "mchen"}, "decision": "ALLOW", "determining": ["policy1"],
  "errors": ["error while evaluating policy `policy2`: `User::\"vk-ext-0042\"` does not have the attribute `team`"]},
]
(out / "policy-decision-log.jsonl").write_text("\n".join(json.dumps(d) for d in dec) + "\n")
(out / "claims-vk-ext-0042.json").write_text(json.dumps({"iss": "https://idp.harborpoint.example/oauth2/lighthouse",
    "aud": "lighthouse-gateway", "preferred_username": "vk-ext-0042", "role": "manager", "idp": "partner",
    "groups": ["vendor-claims-ops"], "note": "partner IdP federation maps role but not team (SAML attribute not released)"}, indent=1) + "\n")
(out / "claims-lwong.json").write_text(json.dumps({"iss": "https://idp.harborpoint.example/oauth2/lighthouse",
    "aud": "lighthouse-gateway", "preferred_username": "lwong", "role": "manager", "team": "payments", "idp": "workforce"}, indent=1) + "\n")
