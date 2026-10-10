# ANSWER: connect/w8-t1 Release 2026.10.06: every caller lands in GeneralSupport

## Approach

Started from the page timing (19:05 deploy), compared flow logs before and after, then read the
deployed artifact and the promote step. Checked the Lambda theory against the same contacts.

## Root cause

`jq -c 'select(.Identifier=="ask-bot")' incident/flow-logs/*.jsonl` shows every non-VIP contact
after 19:05 hitting ask-bot with `"BotAliasArn":"arn:aws:lex:us-east-1:111122223333:bot-alias/..."`
and `"Results":"Error"`, then set-q-general. Before 19:05 there is no ask-bot (DTMF main-menu). The
deployed artifact `release/prod/03-flow-lfg-help-desk-inbound.json` still has the dev account alias.
`pipeline/rewrite.ts` matches only `arn:aws:(connect|lambda):`, so Lex ARNs pass through; 2026.10.06 is
the first release with a Lex reference. All ask-bot error branches go to set-q-general, so contacts
still queue and the password-reset module never runs (self_service_resets drops to 0,
ContactFlowErrors 0 -> 24 per 5 min). Green pipeline: check-refs "skipped (REL-412)", lint is
structural, smoke used DTMF 2 which reaches GeneralSupport through the error branch.
Lambda theory: one timeout at 19:07 and three cold starts; that contact took set-unverified and still
reached ask-bot; errors are 100% of non-VIP contacts at all times after 19:05.

## Fix

Regex now matches any service, and the inventory decides what is rewritten; implemented checkRefs
(every ARN must be the target instance, an inventory resource or an allowed account; paths; embedded;
Metadata); `make release` regenerated release/prod with the prod alias and the gate reports 0 problems;
on the shipped artifact it reports the ask-bot alias. make test passes.

## Trade-offs / what I would do in production

Gate mandatory before approval; native flow test cases that exercise the bot path; smoke call with an
utterance; alarm on ContactFlowErrors after a release with automatic redeploy of the previous artifacts;
Lex alias and IntegrationAssociation managed in IaC per environment.
