# Rubric: connect/w9-t1 Agents stuck in a SAML login loop
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (most rows are guards that already pass on the starter) |
| 2 | Root cause identified | 25 | Full: the new app's default relay state is the instance access URL (lfg-helpdesk.my.connect.aws/ccp-v2) instead of the Connect federation endpoint `https://us-east-1.console.aws.amazon.com/connect/federate/<instance-id>`, so after a successful AssumeRoleWithSAML the browser never calls the federate endpoint, no GetFederationToken happens, Connect has no session, its login page sends the agent back to the IdP: a loop. Partial (10-15): "relay state wrong" without the mechanism. Zero: blames certificates, the session policy, RoleSessionName or users. |
| 3 | Evidence | 20 | Full: HAR POST to signin.aws.amazon.com/saml redirecting to the access URL and then /login; CloudTrail shows AssumeRoleWithSAML today but no GetFederationToken (yesterday both); legacy export's relay state vs new; decoded assertion shows Role/RoleSessionName correct. Partial: one piece. |
| 4 | Red herring handled | 5 | Rules out the Okta 8 h session change: the loop happens on the first sign-in of the shift, Okta SSO events are SUCCESS, Connect sessions (12 h from login) and Okta session lifetime do not interact in this flow; SessionDuration 43200 still within the role's max. |
| 5 | Fix quality | 10 | Relay state set to the federate URL for us-east-1 and the prod instance id (not UAT), optional URL-encoded destination; nothing else changed; verification plan with one pilot agent and CloudTrail GetFederationToken. |
| 6 | Prevention / production | 10 | Concrete: IdP app config as code with a lint for the relay-state format, a synthetic login canary that asserts GetFederationToken, change-template checklist for Connect SSO apps, agent bookmarks pointing at the Okta tile not the access URL. |
Total: 100
