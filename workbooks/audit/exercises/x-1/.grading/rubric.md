# Rubric: audit/x-1 Azure Function cannot reach Gemini: Workload Identity Federation impersonation denied
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 25 | points = 25 * passed / total from grade.sh (most hidden tests are guards against over-broad fixes, which already pass on the starter) |
| 2 | Root cause | 30 | Full: the mapping is google.subject=assertion.sub, and for an Entra managed identity token sub (and oid) is the principal object id 3f9d2c71-..., while the roles/iam.workloadIdentityUser binding names subject/9a41e0b5-..., which is the client id (appid); STS therefore succeeds and impersonation is denied. Partial: "wrong principal in the binding" without the sub/appid distinction. Zero: audience, issuer or Gemini permissions blamed. |
| 3 | Evidence | 15 | Full: quotes the token claims (sub, oid, appid), `az identity show` (principalId vs clientId), the STS principal from the Function or audit log and the binding member; places the failure at the iamcredentials hop, not STS. |
| 4 | Red herring and rejected shortcuts | 15 | Full: explains the two audiences are different hops (Entra resource api://... for the subject token, the provider resource name for STS) and both match; rejects roles/owner, whole-pool or tenant-wide principalSets and a key, with the reason (any identity in the tenant could then use Gemini as ControlPilot). |
| 5 | Production | 15 | Full: binding in IaC with a test like the hidden ones, an alarm on STS/impersonation failures, keep the tenant condition, consider an attribute for the MI resource id (xms_mirid) instead of a GUID, evidence for SEC-2291 (key deleted, audit log of the keyless calls). |
Total: 100
