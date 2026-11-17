# Web storefront release 2026.11.04

- Assistant panel: automatic reconnect. If the stream connection drops before the answer is complete,
  the panel reconnects (up to 3 times) and resumes with Last-Event-ID instead of showing an error.
  The gateway buffers each answer for 60 s and resumes after the given id. (WEB-3391)
- Assistant panel: a fresh SSE parser per connection so a half-received event from a dropped
  connection is discarded. (WEB-3391)
- Assistant panel: enabled React StrictMode in development builds. (WEB-3374)
- Product page: lazy-load review images. (WEB-3350)
