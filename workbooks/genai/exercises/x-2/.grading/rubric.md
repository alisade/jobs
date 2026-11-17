# Rubric: genai/x-2 Human handoff opens the wrong conversation
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: `requestHandoff` is memoized with `useCallback(..., [])` (and the Alt+H effect registers it once with `[]`), so it closes over `active` from the first render: the conversation that was open when the page mounted. Switching updates `activeId` but not the closure, so the button and the shortcut both send the first conversation's id and transcript. Partial (10-15): "stale state" without naming the empty dependency arrays and the first-render capture. Zero: blames the API dedupe or the cache. |
| 3 | Evidence | 20 | Full: DevTools capture shows `State: "c-77452"` on screen while the payload sends `c-77410`, and `Callback ... deps: []`; API log shows the client sent `conversation_id=c-77410` after a page view of c-77452 and the API "does not infer it"; ticket transcript is the tent conversation; release note WEB-3302 "memoized ... registered once". Partial: one or two. |
| 4 | Red herrings ruled out | 5 | The duplicate-request warnings are a consequence (the same old id arrives again, so idempotency returns the old ticket), not the cause; the staleTime change affects the list, and the DevTools capture shows the right conversation rendered while the wrong one is sent. |
| 5 | Fix quality | 10 | Latest-value ref (or correct dependencies) so the handler reads the current conversation and client; the shortcut effect has correct dependencies and a cleanup, so exactly one registration is active. Adding `active` to the deps of only one of the two hooks, or re-registering without cleanup, loses points. |
| 6 | Prevention | 10 | Concrete: turn `react-hooks/exhaustive-deps` into an error and ban disabling it without review, a test that switches conversations before handing off, the server rejecting or flagging a handoff whose conversation is not the session's most recent active one, logging the on-screen id with the request. Partial: generic. |
Total: 100
