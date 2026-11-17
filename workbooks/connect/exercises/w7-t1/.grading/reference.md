# Reference: connect/w7-t1

**Root cause.** Release 2026.10.06 moved the "copy bot context" block from the chat flow into a new flow
module, `lfg-handoff`. Flow modules run with their own data scope: they cannot read the invoking flow's
Lex results (`$.Lex.*`), Lambda results (`$.External.*`), stored customer input, queue metrics, Customer
Profiles or agent assist attributes. Inside the module `$.Lex.IntentName` and
`$.Lex.SessionAttributes.botSummary` resolve to empty, so `SetAttributes` writes empty strings and the
agent app shows nothing. Routing still works because the main chat flow routes on `$.Lex.IntentName`
after the module returns (the parent's Lex data is intact), which is all UAT checked. Voice is unaffected
because it still copies inline.

**Evidence to expect.** Lex conversation logs: chat sessions with `sessionAttributes.botSummary` set.
Flow logs: `ContactFlowName: "lfg-handoff (module)"`, `SetAttributes`, `Parameters: {"lexIntent": "",
"botSummary": "" ...}` vs the voice flow's `SetAttributes` with values. CTRs: chat `Attributes` hold empty
strings plus `handoffSource=bot` and `handoffModuleVersion=1` (proof the module ran). Queue is correct.

**Red herring.** One chat has `InitialContactId != ContactId` and a `RelatedContactId`: that is persistent
chat rehydration. The app reads the current contact; the attributes are already empty in the CTR, so the
loss happens before the app.

**Fix.** In the chat flow, copy the Lex values into contact attributes before `Invoke module`; the module
works from contact attributes (or declared module inputs). Reference: `.grading/solution/`.

**Prevention.** Treat modules like functions with a contract (inputs/outputs), add a handoff test per
channel (Connect's flow test cases or a local simulation in CI), alarm on handoffs with an empty summary.
