# ANSWER: genai/x-2 Human handoff opens the wrong conversation

## Approach

I compared what was on screen with what was sent. The DevTools capture shows the stove conversation
(`c-77452`) rendered, but the network payload of the same click carries `c-77410`, the tent
conversation. So the wrong value is produced in the page before the request. Then I read `ChatPage.tsx`
and reproduced it in a test: switch, then hand off.

## Root cause

A stale closure. Release 2026.10.28 (WEB-3302) memoized the handler as `useCallback(async () => {...},
[])` and registered Alt+H in `useEffect(..., [])`, with `exhaustive-deps` disabled. Both capture `active`
from the first render, which is the conversation open when the page mounted. Switching changes `activeId`
and the rendering, but not the captured value. That is why only customers with more than one
conversation are affected.

Evidence:
- `component-state.txt`: hooks `1 State: "c-77452"` and `4 Callback: f requestHandoff() deps: []`. The
  payload is `{"conversationId":"c-77410","transcript":["customer: Do you have a tent for two..."]}`.
- `handoff-api.log`: `page_view ... /conversations/c-77452` at 14:21:40, then `POST /v1/handoffs ...
  conversation_id=c-77410` at 14:22:51. The log notes that the body id "is exactly what the client sent".
- `ticket-T-48810.md`: the tent transcript arrived for a stove return.

Red herrings: the "duplicate request" warnings come from the API correctly returning the open ticket for
the old id that the client resends. They are a consequence. The staleTime change affects the list cache,
and the capture shows the right conversation on screen.

## Fix

- I keep the latest `{ active, client }` in a ref that is assigned during render. `requestHandoff` is a
  stable `useCallback` that reads the ref.
- The shortcut effect depends on `[shortcuts, requestHandoff]` and returns the unregister function, so
  only one registration is active at a time.
- Verified: `make test` passes, including the repro. I also checked repeated switching, a late message,
  and a new client prop.

## Trade-offs / what I would do in production

- The ref pattern keeps the shortcut registered once. Listing real dependencies would also be correct,
  but it re-registers the shortcut on every message.
- Make `exhaustive-deps` an error, and require review to disable it.
- Add the switch-then-handoff test to CI.
- The API should log the session's active conversation next to the requested one and alert on a
  mismatch.
