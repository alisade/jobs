# awsfde/w4-t1 - After the SPA moved to access tokens, other tenants see Acme's shipments

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Mon: Cognito user pools and federation; Tue: pre token generation; Wed: JWT authorizers and tenant claims)

## Symptom

Brightline Health opened a P1 security ticket this morning: their staff see a shipments list in
Tidewater Ask that is not theirs. Corvid Logistics reported the same an hour later. Acme Foods users
say everything looks normal. Brightline rotated their SAML signing certificate last night and
suspects the federation. Read `evidence/TICKET-5604.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/TICKET-5604.txt` | the customer ticket and the account team's note |
| `evidence/frontend-2026.11.11.diff` | the SPA release deployed this morning |
| `evidence/BH-CHG-2231-saml-cert-rotation.txt` | Brightline's certificate rotation last night |
| `evidence/tokens-decoded.md` | decoded ID and access token payloads Brightline IT captured (fake, unsigned) |
| `config/user-pool.json` | the user pool settings that matter (the `DescribeUserPool` view); edit it as you would with `UpdateUserPool` |
| `config/frontend.json`, `config/lambda-env.json` | SPA runtime config and the API Lambda's environment |
| `tenant_api/` | this checkout: the pre token generation trigger, the tenant resolver, the shipments handler |
| `cognito_sim/` | token issuance with the trigger, the SPA's token choice and the HTTP API JWT authorizer, following the documented Cognito behaviour (see its docstring). Treat it as the environment, not the suspect. |
| `run/` | created by `make setup`: `summary.txt`, `authorizer.log` (claim names per request), `lambda.log` (how the tenant was resolved), `requests.jsonl` |

## Your task

1. Find the root cause and prove it: what each token carries, why Acme looks fine, why it started
   this morning, and why the pilot-era code turned a missing claim into a data exposure.
2. Decide whether the SAML certificate rotation is involved, with evidence.
3. Fix it without reverting the frontend change (sending access tokens to the API is correct):
   the user pool, the trigger and the Lambda, so that every user gets only their own tenant and a
   request without a tenant claim fails closed.
4. Verify with `make test` and `make replay`.
5. Write `ANSWER.md`: root cause with evidence, the exposure statement (which users saw which
   tenant's data), and prevention.

## Acceptance criteria (what the grader checks)

- The pool sends the V2_0 trigger event and the trigger adds `tenant_id` to the ID token and the
  access token; an unmapped user still cannot sign in.
- The resolver has one source (the `tenant_id` claim); no default tenant anywhere; 403 without it.
- Every pilot user is served their own tenant, whether the SPA sends the access token or the ID token.
- `ANSWER.md` names the mechanism (V1_0 customizes only the ID token; the fallback chain ends in
  `DEFAULT_TENANT`) with log and config evidence, and rules out the certificate rotation.

## How to run

```bash
make setup     # shared venv + replay of every pilot user's sign-in and API call into run/
make test
make replay    # after your fix
# from workbooks/: /grade awsfde/w4-t1
make clean
```
