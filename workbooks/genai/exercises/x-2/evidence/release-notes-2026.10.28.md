# Release 2026.10.28

## Web storefront
- My conversations: keyboard shortcut Alt+H to talk to a person. The handoff handler is now memoized so
  the shortcut listener is registered once instead of on every render. (WEB-3302)
- My conversations: TanStack Query staleTime for the conversation list raised from 30 s to 5 min to cut
  API calls. Messages for the open conversation still stream live. (WEB-3297)
- Footer: new store locator link. (WEB-3288)

## Handoff API 4.12
- POST /v1/handoffs is idempotent on conversation_id: if an open ticket exists for that conversation the
  API returns it with 200 instead of creating a duplicate. (HAPI-410)
