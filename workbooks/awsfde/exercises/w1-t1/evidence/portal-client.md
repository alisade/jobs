# Portal client behavior for POST /v1/answer (web app, unchanged since 2026-05)

From `portal/src/api/ask.ts` (summary, the portal is not in this repo):

- Timeout: the browser request is abandoned when API Gateway returns 504 (integration timeout 29 s).
- On HTTP 429, 500, 502 or 504 the portal retries the same question ONCE, 1 s later, then shows
  "Something went wrong".
- On HTTP 503 with a `Retry-After` header the portal does not retry; it shows
  "Tidewater Ask is busy, try again shortly" and re-enables the Ask button after Retry-After seconds.
- On HTTP 400 it shows the validation message from the body.
