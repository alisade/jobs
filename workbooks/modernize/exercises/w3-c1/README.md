# modernize/w3-c1 - Move ClaimDesk authorization from LDAP groups to JWT claims with identical behaviour

**Type:** coding | **Estimate:** 3 hours | **Study plan:** Week 3 (Mon: where legacy authorization hides; Tue-Wed: OIDC, JWT validation, the Okta groups claim; Thu: parity tests)

## Scenario

ClaimDesk authorizes every request from corporate LDAP groups today. Corvane Mutual is moving
the application to Okta: the agent portal will call ClaimDesk with an Okta access token (a JWT),
and the LDAP lookups go away. Security and the business owners signed off on one condition:
**nobody's access changes on cutover day**. Not one more payment approval, not one fewer.

The authorization rules themselves (`ClaimPolicy`) stay exactly as they are. What changes is
where roles come from: `LdapRoleResolver` (today) is replaced by `JwtRoleResolver` (yours).

## What you have

| Path | What it is |
|---|---|
| `src/main/java/.../ClaimPolicy.java` | the rules; do not change them |
| `src/main/java/.../LdapRoleResolver.java` | today's resolver: direct and nested LDAP groups, disabled accounts |
| `src/main/java/.../JwtRoleResolver.java` | the TODO |
| `src/test/resources/corvane.ldif` | a snapshot of the production directory (loaded into an embedded UnboundID LDAP server) |
| `src/test/resources/okta-users.json` | the `groups` claim the Okta authorization server emits per user (direct memberships only) |
| `src/test/java/.../TestIssuer.java` | a local stand-in for Okta: RSA key, JWKS, token minting |

No Okta tenant or network is needed; everything runs in the JVM.

## Okta configuration (agreed with the identity team)

- Custom authorization server, issuer `https://corvane.okta.example/oauth2/aus1claimdesk`, audience `api://claimdesk`.
- Access tokens are RS256, `kid` in the header, keys published in the JWKS (may hold more than one key).
- A `groups` claim filtered to groups starting with `APP_ClaimDesk_`. AD groups are synced into Okta:

| LDAP group | Okta group |
|---|---|
| claims-users | APP_ClaimDesk_Users |
| claims-adjusters | APP_ClaimDesk_Adjusters |
| claims-senior-adjusters | APP_ClaimDesk_SeniorAdjusters |
| claims-managers | APP_ClaimDesk_Managers |
| claims-auditors | APP_ClaimDesk_Auditors |

## Requirements (the contract)

1. `new JwtRoleResolver(JWKSet keys, String issuer, String audience)`; `rolesFor(token)` returns
   roles such that `ClaimPolicy` decides exactly as it does with `LdapRoleResolver` for the same user.
2. Reject (throw `InvalidTokenException`) anything that is not a valid token for this API: any
   algorithm but RS256, a signature not made by a key in the JWKS, wrong `iss`, wrong `aud`,
   expired or not yet valid beyond a clock skew of `MAX_CLOCK_SKEW_SECONDS` (60), malformed input.
3. A valid token with no `groups` claim, or only unknown groups, has no roles (deny), not an error.
   `groups` may be a JSON array or a single string. Group names match exactly.
4. Do not change `ClaimPolicy`, `LdapRoleResolver` or `Role`.
5. `ANSWER.md`: how you proved parity, the differences between LDAP and the token you found and
   how you handled each, and the cutover and rollback plan.

## Acceptance criteria (what the grader checks)

- Hidden parity test: every user in the snapshot x every action x boundary amounts decides the
  same through LDAP and through JWT.
- Hidden token tests: wrong audience, wrong issuer, expiry and not-before with skew, a token
  signed by a foreign key with the same `kid`, `alg: none`, HS256 signed with the public key, garbage
  input, a JWKS with two keys, missing and single-string `groups`, case-different group names.
- `ANSWER.md` covers the semantic gaps between the two sources and the rollout.

## How to run

```bash
make setup      # JDK 21 + Maven, downloads artifacts once
make test       # visible tests (the JWT one fails until you implement the resolver)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w3-c1
make clean
```
