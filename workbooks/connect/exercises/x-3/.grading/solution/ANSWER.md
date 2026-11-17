# ANSWER: connect/x-3 Lex fallbacks after a slot type change

## Approach

Compared analytics before/after version 8, diffed the two deployed exports, then read conversation logs for
the missed utterances and the slot values, and replayed the eval set with make evals.

## Root cause

`diff -ru scripts/fixtures/bot-version-7 scripts/fixtures/bot-version-8`: SystemName values became CI codes
with no synonyms and resolutionStrategy ORIGINAL_VALUE (plus the voice change). Logs on 10-06: "sap is down"
missedUtterance true, best alternative ReportOutage nluConfidence 0.25 (< 0.40); "reset my okta password" ->
ResetPassword with empty System and dialogAction ElicitSlot System. On 10-04 the same utterances resolved
System to "Okta"/"VPN" with high confidence. Analytics: fallback 3.7% -> 22.8%, elicitation failures 19 ->
2,711. make evals on the current bot: 5/16. Voice is TTS only; threshold 0.25 would misroute instead.

## Fix

Kept the CI codes as values, added spoken names as synonyms (okta, okta verify, sso, single sign on; workday;
sap, sap gui, ecc; outlook, email, exchange, mail; vpn, globalprotect, global protect, remote access),
TOP_RESOLUTION. make evals 16/16; make test passes; threshold unchanged.

## Trade-offs / what I would do in production

Roll the live alias back to version 7 immediately; gate alias moves on test sets; keep evals with the export in
CI; alarm on missed utterances; long term the CMDB mapping could live in the code hook, but codes-as-values with
synonyms keeps one source of truth.
