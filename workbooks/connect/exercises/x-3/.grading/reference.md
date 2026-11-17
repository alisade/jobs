# Reference: connect/x-3

Root cause: HelpDeskBot version 8 replaced the SystemName slot type values (Okta, Workday, SAP, Outlook,
VPN with spoken synonyms, TOP_RESOLUTION) by CMDB codes with no synonyms and ORIGINAL_VALUE, to feed
cmdb_ci in ServiceNow. Lex uses slot values to recognize slots and, through them, to classify utterances
that are built around the slot. Callers never say "CI-GLOBALPROTECT", so:
- "{System} is down" style utterances lose most of their match and fall under the 0.40 threshold ->
  FallbackIntent (missedUtterance true for "vpn is down", "is outlook down", "sap is down");
- intents that still match through slot-less utterances ("reset my okta password" -> ResetPassword) leave
  System empty, so the bot elicits it, the caller says "Okta", which is not a value either, and elicitation
  fails (system_slot_elicitation_failures 19 -> 2,711 per day).

Red herrings: the Ruth/generative voice is text-to-speech only; lowering the threshold to 0.25 turns
fallbacks into wrong guesses and still leaves the System slot empty.

Fix (`.grading/solution/bot/`): keep the CMDB codes as sampleValue, add the spoken names as synonyms,
TOP_RESOLUTION so the interpreted value is the code. Immediate mitigation in production: move the live
alias back to version 7 while the fix goes through test sets.

Prevention: test sets / test workbench run against every new bot version before the alias moves; the eval
set lives in git next to the export and runs in CI; alarm on missed-utterance rate; slot type changes need
conversation-design review.
