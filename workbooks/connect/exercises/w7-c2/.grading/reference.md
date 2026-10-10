# Reference: connect/w7-c2

Reference code: `.grading/solution/src/` (`AgentAssistApp.tsx`, `rank.ts`, `guide.ts`, `api.ts`).

Points an interviewer looks for:

- **Lifecycle.** A ref holds the contact on screen. `onConnected` sets it before awaiting
  `getAttributes` and drops results that arrive after another contact connected; `onCleared` acts only
  on the current contact. Handlers are stable (`useCallback`) so `off*` receives the same reference.
- **Least data.** `getAttributes(contactId, HANDOFF_KEYS)` instead of `"*"`: contact attributes are
  readable by anything with access to the contact, and other teams put sensitive values there.
- **Guide gating.** Identity verification is pre-checked only when the bot or portal verified the
  caller; resolve requires every required step.
- **Ranking.** Normalize, default-deny entitlement, floor, dedupe keeping the best score (tie: agent
  assist), stable sort, cap. In production entitlements come from the agent's IdP groups or Connect
  hierarchy, and the same metadata drives KB retrieval filters so the backend never returns content
  the agent cannot see (filtering in the UI alone is not access control).
- **Backend.** The app calls LFG's API (API Gateway + Lambda with the agent's identity), never
  ServiceNow directly; failures are visible and retryable.
- **Build vs configure.** Step-by-step guides (views + Show view block) cover simple checklists with no
  code; a third-party app is justified here by cross-source ranking and the ServiceNow write-back.
