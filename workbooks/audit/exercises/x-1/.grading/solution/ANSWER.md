# ANSWER: audit/x-1 Workload Identity Federation impersonation denied

## Approach

Walked the hops in order with incident/ and config/: IMDS token, STS exchange, impersonation, Gemini.
The Function log and the STS audit entry show STS returned 200; the failure is at iamcredentials.

## Root cause

The provider maps google.subject=assertion.sub. The token's sub (and oid) is
3f9d2c71-8a4b-4e6f-b1d2-6c7e9a0f5b84, which `az identity show` lists as principalId. STS issued a
token for principal://.../subject/3f9d2c71-.... The service account binding grants
roles/iam.workloadIdentityUser to principal://.../subject/9a41e0b5-2c7d-4f38-8e19-d5b6a3c0f271,
which is the clientId (appid). The principal does not match, so getAccessToken is denied.

The audience theory is wrong: the Entra token aud (api://b6d0a3f2-...) is checked against the
provider's allowed_audiences and matches; the credential config audience is the provider resource
name that STS checks, and it matches too. STS succeeded.

## Fix

Changed the binding member to subject/3f9d2c71-8a4b-4e6f-b1d2-6c7e9a0f5b84. make sim: RESULT OK.
Another identity in the tenant, another tenant and another audience are still denied. roles/owner or
a pool-wide principalSet would let any identity in the tenant call Gemini as ControlPilot; a key
would reopen SEC-2291.

## Trade-offs / what I would do in production

Keep the binding in Terraform with a policy test; alarm on STS and impersonation failures; consider
mapping xms_mirid (the MI resource id) to an attribute so the binding is readable; keep the tenant
condition; record for SEC-2291 that the old key is deleted and that audit logs show keyless calls.
