# Reference: connect/w1-c2

Reference stack: `.grading/solution/lib/helpdesk-stack.ts`.

What matters:

- `Fn::Sub` with a variables map turns `${QueueGeneralSupport}` into `{"Fn::GetAtt": [QueueGeneralSupport..., "QueueArn"]}`
  at deploy time, so the same template text deploys to every account. String replacement at synth
  time bakes one account's ARNs into the artifact and is the root of most "prod calls dev" incidents.
- Validate placeholders at synth: a missing variable in `Fn::Sub` only fails in CloudFormation, after
  the change set is approved; a typo that matches a literal string can even succeed and break calls.
- Hours overrides (`HoursOfOperationOverrides`, OverrideType STANDARD | OPEN | CLOSED) model holidays
  declaratively; keep the 24x7 hours free of closures.
- Routing profile `QueueConfigs` are per channel: forgetting CHAT means chats never route even though
  the profile has chat concurrency. Delay applies per queue per profile: senior analysts take General
  only after it has waited 30 s.
- Lex: Connect should use an alias on a numbered version; TestBotAlias is throttled and not for
  production. The FallbackIntent is required in every locale.
- Production gaps worth naming: phone numbers (claim/port; `AWS::Connect::PhoneNumber` exists but
  porting is a process), agent users come from the IdP via SAML, contact flows have no alias in CFN
  (modules do), console edits drift from the template, and the instance should be retained.
