# connect/w9-t1 - Agents stuck in a SAML login loop after the Okta migration

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 9 (SAML 2.0 SSO for Connect: IdP-initiated flow, relay state, RoleSessionName, GetFederationToken, session duration)

## Symptom

The morning after the IAM team moved the "Amazon Connect - Help Desk" Okta app to a new Okta
org, Monterrey agents clicking the tile bounce between Okta, AWS and a Connect page that tells
them to sign in through their identity provider, then land back on the Okta dashboard. The IAM
team says the app is a 1:1 copy and CloudTrail shows `AssumeRoleWithSAML` succeeding; they
suspect the CISO's Okta session-lifetime change made the same night. The queue is building.
Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | PAGE and thread, change records, a HAR summary of one agent's login with the posted form fields, CloudTrail events from yesterday and today, Okta system log, the legacy Okta org's app export |
| `idp/okta-connect-app.json` | the new Okta SAML app as exported (what you may fix) |
| `iam/role-LFG-ConnectAgents.json` | the IAM role agents assume: trust policy, federation policy, max session |
| `config/connect-instance.json`, `config/users-sample.csv` | the Connect instance (SAML identity) and a sample of its users |
| `tools/saml.js` | `make decode` (decode the captured SAMLResponse), `make attrs` (evaluate the attribute statements per user) |

## Your task

1. Find the root cause. Walk the IdP-initiated SAML flow hop by hop (Okta -> AWS sign-in ->
   relay state -> Connect) and show where it breaks, with evidence from the HAR, CloudTrail and
   the two app exports.
2. Rule out the red herring with a reason.
3. Fix the configuration (only what is broken; the rest of the chain must stay valid).
4. Write `ANSWER.md`: Approach, Root cause (evidence excerpts), Fix (and how you would verify it
   in production), Trade-offs / prevention.

## Acceptance criteria (what the grader checks)

- The app's default relay state uses the documented Connect federation format for this
  instance's Region and production instance id; any deep-link destination is URL-encoded.
- ACS URL, audience, Role and RoleSessionName attributes, the trust policy, the
  `connect:GetFederationToken` permission and the session duration stay valid.
- `ANSWER.md` explains the mechanism (why `AssumeRoleWithSAML` succeeds but agents never reach
  Connect) with evidence, and why the admin tile still works.

## How to run

```bash
make setup     # links the toolchain, writes incident/
make decode    # the SAML assertion from the HAR
make attrs     # attribute statements evaluated for each sample user
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w9-t1
make clean
```
