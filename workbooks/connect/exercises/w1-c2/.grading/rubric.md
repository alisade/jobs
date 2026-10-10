# Rubric: connect/w1-c2 Help desk instance as code (CDK)
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Environment safety | 15 | Full: flow content via Fn::Sub with GetAtt/Ref tokens, Lambda ARNs from pseudo parameters, nothing account-specific in code, unknown env/placeholder/queue fail at synth with a useful message. Partial: tokens used but validation missing. Zero: string replacement of ARNs survives anywhere. |
| 3 | Connect modelling | 10 | Holidays as CLOSED overrides on staffed hours only, 24x7 hours for major incidents, both channels per queue config, cross-channel behavior set deliberately, Lex alias on a numbered version (not TestBotAlias). |
| 4 | Code quality | 5 | Small typed helpers, config-driven loops, no duplicated blocks, outputs for downstream stacks. |
| 5 | ANSWER.md production view | 15 | Full: names real gaps and positions (phone number claiming and porting outside CFN or via AWS::Connect::PhoneNumber with care, users from SAML/IdP not CFN, console drift on flows, Lex locale build times, retained instance and DeletionPolicy, separate stacks for long-lived vs fast-changing resources), and a promotion story (template + Fn::Sub per env, or export/rewrite pipeline from week 8). Partial: generic. |
Total: 100
