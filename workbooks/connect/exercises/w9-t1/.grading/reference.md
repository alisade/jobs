# Reference: connect/w9-t1

Root cause: CHG0031177 recreated the Connect Okta app and set `defaultRelayState` to the
instance access URL from the Connect console (`https://lfg-helpdesk.my.connect.aws/ccp-v2`).
For a SAML instance the relay state must be the federation endpoint
`https://<region>.console.aws.amazon.com/connect/federate/<instance-id>` (optionally
`?destination=%2Fccp-v2` URL-encoded). That endpoint is what calls
`connect:GetFederationToken` with the assumed-role session (RoleSessionName = Connect username)
and creates the Connect session. With the access URL as relay state, AWS sign-in accepts the
assertion (AssumeRoleWithSAML succeeds, as the IAM team saw), redirects to the access URL, Connect
has no session, its login page tells the agent to sign in through the IdP, the agent clicks
back to Okta: the loop.

Evidence: HAR (POST /saml -> 302 to my.connect.aws/ccp-v2 -> /login); CloudTrail today has
only AssumeRoleWithSAML, yesterday each was followed by GetFederationToken; the legacy export's
relay state is the federate URL. The two agents still working had a live Connect session from
yesterday. The admin tile works because its relay state is the console (no Connect federation).

Red herring: the Okta session-lifetime change (12 h -> 8 h) affects re-authentication to Okta,
not the hop from AWS sign-in to Connect; it cannot explain a loop on the first sign-in.

Fix: `defaultRelayState` = `https://us-east-1.console.aws.amazon.com/connect/federate/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f?destination=%2Fccp-v2`.
Verify with one agent: CloudTrail AssumeRoleWithSAML followed by GetFederationToken, CCP loads.

Prevention: manage the IdP apps as code (Okta Terraform provider) with a lint on the relay-state
format and instance id, a synthetic SSO canary per instance, and a CAB checklist for Connect SSO.
