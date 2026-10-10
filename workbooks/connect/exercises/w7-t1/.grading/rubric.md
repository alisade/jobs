# Rubric: connect/w7-t1 Bot-to-agent handoff loses context on chat
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: the chat flow's new shared module `lfg-handoff` copies `$.Lex.IntentName` / `$.Lex.SessionAttributes.*` into contact attributes, but a flow module cannot read the invoking flow's Lex data (nor $.External, stored customer input, queue metrics), so the values resolve empty; voice still copies inline in the main flow. UAT only checked routing, which uses `$.Lex.IntentName` in the main flow and still works. Partial (10-15): "the module breaks it" without the module data-scope mechanism. Zero: blames the agent app, Lex, or persistent chat. |
| 3 | Evidence | 20 | Full: at least three quoted pieces: Lex logs show sessionAttributes populated for the chat sessions; flow log `SetAttributes` inside `lfg-handoff (module)` with empty values vs the voice `SetAttributes` with values; CTR Attributes empty strings on chat; routing correct. Partial: one or two pieces. |
| 4 | Red herring ruled out | 5 | InitialContactId != ContactId comes from persistent chat rehydration (RelatedContactId); the app reads the current ContactId and the attributes are already empty in the CTR, so the source is upstream of the app. |
| 5 | Fix quality | 10 | Copy bot context into contact attributes in the main flow before invoking the module (or pass it as module input), module reads only attributes/inputs, voice and chat parity; no hard-coded values; routing unchanged. |
| 6 | Prevention | 10 | Concrete: module input/output contracts, per-channel handoff test cases (Connect flow test cases / simulation in CI), voice adopting the module with the same tests, metric/alarm on handoffs with empty botSummary. Partial: generic "more testing". |
Total: 100
