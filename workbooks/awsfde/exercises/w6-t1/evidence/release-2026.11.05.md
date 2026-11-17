# Tidewater Ask web release 2026.11.05 (deployed 2026-11-12 06:00 UTC)

- ASK-377 Cost: cache GET responses from the catalog API at the edge for 5 minutes. New cache policy
  tw-api-short-cache (MinTTL 0, DefaultTTL 300, MaxTTL 3600, all query strings in the key) attached
  to the /api/* behavior of distribution E2TIDEWATER9K. Catalog origin p50 load down 70% in staging.
- ASK-380 Security review: SessionLifetimeInMinutes for embedded analytics reduced from 600 to 15.
- ASK-381 AllowedDomains now includes https://*.portal.tidewater.example for the partner portals.
- Embed endpoint moved from /analytics/embed-url (API Gateway domain) to /api/analytics/embed-url
  behind CloudFront so the SPA calls a same-origin path (removes the CORS preflight).
