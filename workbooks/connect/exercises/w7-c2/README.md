# connect/w7-c2 - Agent workspace app: handoff context, guided resolution and agent assist

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 7 (agent workspace: views, step-by-step guides, third-party apps; agent assist; bot-to-agent handoff); Week 5 (knowledge retrieval)

## Scenario

When LFG's Lex bot (voice or chat) cannot finish a request, the flow copies the bot's context into
contact attributes and transfers to the help desk queue. Agents work in the Amazon Connect agent
workspace, where LFG embeds a third-party app ("Help desk assistant") next to the contact. A
hackathon prototype exists. In the pilot, agents complained that it showed the previous caller's
summary after a chat ended, crashed when the bot sent half-formed slot data, suggested an
Executive Office procedure to a contractor agent, listed the same article twice, and silently
"resolved" incidents that ServiceNow had rejected. Security also found that it requested every
contact attribute (including a fraud-team field holding an SSN).

## What you have

| Path | What it is |
|---|---|
| `src/workspace.ts` | `ContactEventSource`: the slice of the workspace SDK the app uses. It mirrors the Amazon Connect SDK `ContactClient` (`@amazon-connect/contact`): `onConnected/offConnected`, `onCleared/offCleared` (handler gets `{contactId, initialContactId, type, subtype}`), `getAttributes(contactId, keys | "*")`. `HANDOFF_KEYS` lists the attributes the flow sets. |
| `src/AgentAssistApp.tsx` | the React app (prototype) |
| `src/rank.ts` | merges knowledge suggestions from agent assist and a Bedrock KB Retrieve call |
| `src/guide.ts` | picks the guided-resolution checklist for the bot intent |
| `src/api.ts` | client for LFG's backend (API Gateway + Lambda) that updates the ServiceNow incident |
| `guides/guides.json` | checklists per intent (`_default` for anything else) |
| `fixtures/` | recorded agent-assist `GetRecommendations` and Bedrock `Retrieve` responses, and the KB article catalog (contentId -> department) |
| `tests/fakeWorkspace.ts` | fake `ContactEventSource` that fires lifecycle events inside React `act()` |

## Requirements

Handoff context
1. On `connected`, request only `HANDOFF_KEYS` (never `"*"`) and show: channel, bot summary, intent,
   slots (from the `lexSlots` JSON string; malformed JSON must not crash: show "Slot data unavailable"),
   incident number, a VIP flag, and an alert when `callerVerified` is not `"true"`.
2. On `cleared` for the contact on screen, return to "Waiting for a contact". A `cleared` event for a
   different contact (chat concurrency) changes nothing. A newly connected contact replaces the context
   and resets the checklist.
3. Subscribe once; unsubscribe (`offConnected`, `offCleared`) on unmount.

Guided resolution
4. Checklist for the intent (`guideFor`), default guide for unknown or missing intents. Steps marked
   `autoWhenVerified` start checked for verified callers. "Resolve incident" is enabled only when every
   required step is checked and an incident exists.
5. Resolve calls the backend with `state: "6"`, work notes that list the completed steps, and the bot
   summary as close notes. Show success; on failure show an alert and leave the button enabled for retry.

Knowledge suggestions (`rankSuggestions`)
6. Normalize both sources to `{articleId, title, excerpt, score, source}` (agent assist content id ->
   catalog article id; KB `metadata.articleId`).
7. Drop articles the agent is not entitled to: department `all` or in the agent's `departments`; an
   unknown department is not entitled. Drop scores below `minScore` (default 0.4).
8. Dedupe by article (keep the higher score; on a tie prefer agent assist). Sort by score descending,
   then source, then id. Cap at `max` (default 5). A suggestion failure must not break the panel.

Backend (`createIncidentApi`)
9. `PATCH {baseUrl}/incidents/{sysId}` with `Authorization: Bearer <token>`; reject a malformed
   sys_id (32 hex chars) before sending; throw on non-2xx.

## Acceptance criteria (what the grader checks)

- Context rendering, least-privilege attribute request, no leakage of unrelated attributes.
- Robust to malformed slots, unverified callers, concurrent contacts, clears for other contacts, unmount.
- Checklist gating, resolve payload, failure handling and retry.
- Ranking: dedupe, entitlement, floor, order, cap; unknown department excluded.
- Backend client: method, auth, validation, errors.
- `ANSWER.md`: how you would ship this in the real workspace (app registration, permissions, SSO to the
  backend, where entitlements come from).

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests (jsdom)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w7-c2
make clean
```

Real-world notes: third-party apps are registered in the Connect admin website and shown in the agent
workspace in an iframe; the Amazon Connect SDK (`@amazon-connect/app`, `@amazon-connect/contact`) gives
them contact and agent events. Step-by-step guides (views shown by the "Show view" flow block) are the
no-code alternative for simple checklists. See the Week 7 study guide.
