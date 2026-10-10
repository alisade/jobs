# Rubric: connect/x-3 Lex fallbacks after a slot type change
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: version 8 replaced the SystemName slot type values (Okta, Outlook, VPN... with synonyms) by CMDB codes with no synonyms and switched resolution to original value; callers never say "CI-GLOBALPROTECT", so the System slot is never recognized: utterances built around {System} ("{System} is down") lose confidence and fall below 0.40 to FallbackIntent, and intents that still match leave System empty, so the bot re-elicits it and fails. Partial (10-15): "slot values changed" without the recognition/confidence mechanism. Zero: voice, threshold, or "Lex is flaky". |
| 3 | Evidence | 20 | Full: export diff lines, conversation-log excerpts before/after (nluConfidence drop, missedUtterance true for outage statements, empty System slot and ElicitSlot), analytics (fallback 3.7% -> 22.8%, slot elicitation failures 19 -> 2,711), make evals before/after. Partial: one or two pieces. |
| 4 | Red herrings handled | 5 | Voice change affects TTS only, not NLU; lowering the threshold to 0.25 would turn fallbacks into low-confidence guesses (more misrouting) and still leave System empty. |
| 5 | Fix quality | 10 | CMDB code kept as the slot value with the spoken names as synonyms and TOP_RESOLUTION (code reaches ServiceNow, callers are understood); threshold unchanged; no utterances hard-coded per CI code; synonyms reasonable (email/exchange/mail, globalprotect/remote access, sso). Alternative accepted: human values + code mapping in the code hook, if justified in ANSWER.md (it fails the code-as-value test). |
| 6 | Prevention / production | 10 | Concrete: test sets / test workbench run on the new bot version before moving the live alias; eval set kept in git and in CI with the export; bot versions + alias rollback (move live back to 7) as the immediate mitigation; analytics alarms on missed-utterance rate; slot type changes reviewed by the conversation designers, not only ITSM. Partial: generic. |
Total: 100
