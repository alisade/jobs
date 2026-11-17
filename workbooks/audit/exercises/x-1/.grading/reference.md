# Reference: audit/x-1

**Path.** IMDS issues the token (aud `api://b6d0a3f2-...`, matches `resource=` in the credential
config). STS accepts it: issuer `https://sts.windows.net/<tenant>/` matches, the aud is in
`allowed_audiences`, the tenant condition holds, and `google.subject=assertion.sub` yields
`principal://.../subject/3f9d2c71-...` (logged by the Function and by the STS audit entry).
Impersonation fails: the service account's `roles/iam.workloadIdentityUser` binding grants
`principal://.../subject/9a41e0b5-...`.

**Root cause.** For a managed identity token, `sub` and `oid` are the identity's principal (object) id
(`az identity show` principalId 3f9d2c71-...); `appid` is its client id (clientId 9a41e0b5-...). The
binding was written with the client id, the value most people copy from the portal, so the federated
principal does not match it.

**Red herring.** Two different audiences on two hops are expected: the Entra token's aud is the Entra
application the token is requested for (`api://...`), the credential config's `audience` is the
provider resource name STS validates. Both match their checks; STS returned 200.

**Fix** (`.grading/solution/config/sa-iam-policy.json`): replace the member with
`principal://iam.googleapis.com/projects/418203557719/locations/global/workloadIdentityPools/azure-mfh/subject/3f9d2c71-8a4b-4e6f-b1d2-6c7e9a0f5b84`.
Equivalent: map `google.subject=assertion.appid` and keep the client-id binding, or map an attribute and
bind a principalSet for that single value; either way exactly one identity. Wrong: `roles/owner`,
`principalSet://.../*`, or a tenant-wide attribute set, which let any identity in the tenant act as
ControlPilot; or going back to a key, which reopens SEC-2291.
