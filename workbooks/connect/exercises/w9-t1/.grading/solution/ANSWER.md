# ANSWER: connect/w9-t1 Agents stuck in a SAML login loop

## Approach

Walked the IdP-initiated flow in the HAR: Okta SSO OK, POST to signin.aws.amazon.com/saml OK,
then a redirect to the Connect access URL and its /login page instead of the federate endpoint.
Compared the new app export with the legacy one, decoded the assertion (`make decode`) and checked
the attributes (`make attrs`), then compared CloudTrail for yesterday and today.

## Root cause

The new Okta app's defaultRelayState is `https://lfg-helpdesk.my.connect.aws/ccp-v2` (the access
URL). It must be the Connect federation URL `https://us-east-1.console.aws.amazon.com/connect/federate/5f0c4a7e-...`,
which is what calls GetFederationToken and creates the Connect session.
- HAR: `POST 302 https://signin.aws.amazon.com/saml -> https://lfg-helpdesk.my.connect.aws/ccp-v2`, then
  `-> /login?redirect=%2Fccp-v2` ("Log in through your identity provider").
- CloudTrail 2026-10-07: AssumeRoleWithSAML then GetFederationToken per agent; 2026-10-08: AssumeRoleWithSAML
  only, repeated every ~15-40 s per agent (the loop).
- okta-app-legacy-export.json relayState = `.../connect/federate/5f0c4a7e-...?destination=%2Fccp-v2`.
- Decoded assertion: Role pair, RoleSessionName=mrios (matches the Connect username), SessionDuration 43200.
The two working agents had live sessions from yesterday; the admin tile's relay state is the console.

Red herring: the 8 h Okta session lifetime. Okta sso events are SUCCESS and the loop occurs on the
first sign-in; session lifetime does not touch the AWS -> Connect hop.

## Fix

idp/okta-connect-app.json defaultRelayState ->
`https://us-east-1.console.aws.amazon.com/connect/federate/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f?destination=%2Fccp-v2`.
Verify: one Monterrey agent signs in, CloudTrail shows GetFederationToken, CCP loads; then announce.

## Trade-offs / what I would do in production

Okta apps as code with a relay-state lint, an SSO canary per instance asserting GetFederationToken,
and a CAB checklist for Connect SSO changes.
