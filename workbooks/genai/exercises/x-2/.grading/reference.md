# Reference: genai/x-2

## Root cause
WEB-3302 memoized the handoff handler with `useCallback(async () => {...}, [])` and registered the Alt+H
shortcut in `useEffect(..., [])`, with the lint rule disabled. Both close over the values from the first
render, including `active`: the conversation open when the page mounted. Switching conversations updates
`activeId` and the rendering, but not the closure, so every handoff (button or shortcut) sends the first
conversation's id and transcript. It only shows for customers with two or more conversations.

## Evidence
- component-state.txt: `State: "c-77452"` (stove on screen) and `Callback: f requestHandoff() deps: []`,
  while the network payload is `{"conversationId":"c-77410", ... tent ...}`.
- handoff-api.log: page view of `c-77452`, then POSTs with `conversation_id=c-77410`; "the API does not
  infer it".
- ticket-T-48810.md: the tent transcript.

## Red herrings
- "duplicate request" warnings: the client keeps sending the old id, so idempotency (HAPI-410) correctly
  returns the open ticket for that id. A consequence, not the cause.
- staleTime: the list cache does not decide which id is sent; the DevTools capture shows the correct
  conversation rendered.

## Fix
Keep the latest `active` and `client` in a ref updated during render, read the ref inside a stable
`useCallback`, and register the shortcut in an effect with `[shortcuts, requestHandoff]` that returns the
unregister function. Alternative: list the real dependencies (`active`, `client`) on both hooks and rely
on the effect cleanup to re-register; correct, but it re-registers on every message.

## Prevention
`react-hooks/exhaustive-deps` as an error, a test that switches before handing off, the server logging
or rejecting handoffs whose conversation is not the session's active one, and sending the on-screen id
in telemetry.
