# SUP-7781 - Handoff tickets show the wrong conversation

Reported 2026-11-02 by the Kestrel contact-center team lead. Assigned to you (web storefront).

> **Rosa (contact center):** Since last week, when a customer presses "Talk to a person" on the "My
> conversations" page, the ticket my agents get is often for a DIFFERENT conversation, usually an older
> one from the same session. Example: customer wanted a return for a leaking camp stove (order 1182),
> our ticket T-48810 showed their tent question from earlier. The agent asked about tents and the
> customer left angry. Agents now ask every customer to repeat everything.
>
> **Omar (handoff API):** Our logs show "duplicate request" warnings for these customers. The API is
> idempotent on conversation_id since 2026-10-28, so a second handoff for the same conversation returns
> the existing ticket. Maybe the dedupe key is wrong and we merge tickets?
>
> **Jun (web):** We also raised the TanStack Query staleTime for conversations to 5 minutes in the same
> release. Could the page be showing cached data?
>
> **Rosa:** It only seems to happen when the customer had more than one conversation open in the session.

## Files

| File | What it is |
|---|---|
| `ticket-T-48810.md` | the ticket the agent received |
| `handoff-api.log` | handoff API log for the session |
| `component-state.txt` | React DevTools capture of the page at the moment of the second handoff |
| `release-notes-2026.10.28.md` | web and API release notes |
