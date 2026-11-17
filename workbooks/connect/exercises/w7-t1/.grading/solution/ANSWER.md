# ANSWER: connect/w7-t1 Bot-to-agent handoff loses context on chat

## Approach

Compared one voice and one chat contact end to end: Lex log -> flow log -> CTR -> panel capture.

## Root cause

The 2026.10.06 release moved the context copy into the new module lfg-handoff, and a flow module cannot
read the invoking flow's Lex data. Lex logs show the chat sessions with sessionAttributes.botSummary set
("Password expired while travelling; ..."). The flow log for the same ContactId shows
ContactFlowName "lfg-handoff (module)", SetAttributes with Parameters {"lexIntent":"","botSummary":"",...},
while the voice flow's SetAttributes has the values. Chat CTR Attributes: empty strings, handoffSource=bot,
handoffModuleVersion=1. Routing is right because the parent routes on $.Lex.IntentName after the module,
which is all UAT tested; voice still copies inline. The InitialContactId/RelatedContactId difference is
persistent chat rehydration and not involved: the CTR attributes are already empty.

## Fix

Chat flow copies $.Lex.IntentName and the session attributes into contact attributes before invoking the
module; the module now only tags the contact (handoffModuleVersion=2) and uses attributes. make lint clean,
make test green, make bundle shows the chat summary in the panel capture.

## Trade-offs / what I would do in production

Give the module explicit inputs, move voice onto it with the same tests, add per-channel handoff test cases
to CI, alarm on handoffs where botSummary is empty.
