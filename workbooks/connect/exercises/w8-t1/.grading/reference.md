# Reference: connect/w8-t1

Root cause: release 2026.10.06 replaced the DTMF menu with a `ConnectParticipantWithLexBot`
block (`ask-bot`). The pipeline's promote step (`pipeline/rewrite.ts`) only matched
`arn:aws:(connect|lambda):...` tokens, so the Lex V2 bot alias ARN passed through unchanged and
prod shipped `arn:aws:lex:us-east-1:111122223333:bot-alias/...` (the DEV account). The prod
instance has no access to that alias, the block fails on every contact (flow logs: `ask-bot`
`Results: Error` with the dev `BotAliasArn` from 19:05; `ContactFlowErrors` 0 -> 20+ per 5 min),
and all three of its error branches go to `set-q-general`. VIPs are routed before the bot, so
they look fine.

Why everything was green: `check-refs` was never implemented (pipeline log "skipped"), the lint
is structural only, and the smoke call pressed DTMF 2, which reaches GeneralSupport through the
error branch whether or not the bot works.

Red herring: identify-caller had three cold starts and one timeout at 19:07 after its own code
deploy; that contact took `set-unverified` and still reached `ask-bot`; bot errors are 100% of
non-VIP contacts after 19:05 independent of the Lambda result.

Fix: `.grading/solution/pipeline/rewrite.ts` (any-service ARN regex; the inventory decides),
`.grading/solution/pipeline/check-refs.ts`, and the regenerated `release/prod`.

Production follow-ups: make the gate mandatory; native flow test cases (`AWS::Connect::TestCase`,
`StartTestCaseExecution`) that drive the bot path; synthetic call with an utterance; alarm on
`ContactFlowErrors` after release with automatic redeploy of the previous artifacts; manage the
Lex alias association (`AWS::Connect::IntegrationAssociation`) and alias promotion in IaC.
