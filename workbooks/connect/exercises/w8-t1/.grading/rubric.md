# Rubric: connect/w8-t1 Release 2026.10.06: every caller lands in GeneralSupport
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the new ConnectParticipantWithLexBot block (ask-bot) references the DEV HelpDeskBot live alias (account 111122223333) because promote's ARN regex only matched connect and lambda ARNs; release 2026.10.06 was the first release with a Lex reference, so the gap never showed before; the prod instance cannot use that alias, the block errors on every contact and its error branches route to GeneralSupport, so self-service never runs. Partial (10-15): "flow points at dev Lex" without the regex mechanism or without explaining why calls still reached a queue. Zero: Lambda cold starts, capacity or staffing. |
| 3 | Evidence | 20 | Full: at least three quoted pieces: flow log ask-bot Results Error with the dev BotAliasArn from 19:05 on (DTMF menu before), the artifact line, the regex in rewrite.ts, ContactFlowErrors jump at 19:05, pipeline log showing check-refs skipped and a smoke test that used DTMF 2 (which lands in GeneralSupport whether or not the bot works). Partial: one or two pieces. Zero: assertion only. |
| 4 | Red herring handled | 5 | Rules out identify-caller: one timeout at 19:07 plus three cold starts, contacts still continued (set-unverified path), bot errors are 100% of non-VIP contacts after 19:05 regardless of the Lambda result. |
| 5 | Fix quality | 10 | Regex covers any service and the inventory decides what is rewritten; release regenerated; check-refs implemented with paths, embedded ARNs, Metadata, qualified Lambdas, allow-listed accounts; release.ts exits non-zero on problems. No hand-editing of just the one ARN. |
| 6 | Prevention / production | 10 | Concrete: gate in the pipeline, a synthetic call that exercises the bot (spoken/text utterance via native flow test cases, not just DTMF 2), alarm on ContactFlowErrors > 0 for N minutes after a release with automatic rollback to the previous artifacts, IntegrationAssociation for the prod alias in IaC, Lex alias promotion as part of the same release. Partial: generic "add tests". |
Total: 100
