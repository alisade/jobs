# Reference: awsfde/w6-t1

**Mechanism.** Release 2026.11.05 put the embed endpoint at `/api/analytics/embed-url` behind
CloudFront. The `/api/*` behavior uses `tw-api-short-cache` (MinTTL 0, DefaultTTL 300, all query
strings, no headers in the key), created by ASK-377 for the catalog API. The Lambda returns no
`Cache-Control`, so CloudFront applies DefaultTTL 300 and caches the first response. The cache key
has no identity in it, so every page load for the next 5 minutes, any user, any tenant, gets the
same embed URL. Embed URLs are single use (GenerateEmbedUrl API reference: valid 5 minutes, cannot be
re-used once redeemed), so the first browser to redeem wins and every other load is blank.

**Cross-tenant view.** At 09:45:34 Acme (load-063) missed the cache and got a fresh Acme URL; 0.1 s
later Corvid (load-064) got the same URL from the edge. Corvid's browser redeemed first (redeem delay
200 ms vs 1200 ms), so Corvid's portal showed a session with Acme's tenant tag and data; Acme's
redeem then failed with already_used.

**Evidence.** cloudfront-access.log: 64 embed requests, 53 Hit, 11 Miss; lambda.log: 11 invocations;
quicksight-embed.log: 53 already_used and one ok with data_tenant acme-foods for viewer corvid-logistics.

**Red herrings.** ASK-380 (15-minute session lifetime) explains Brightline's logout complaint and is
intended; the wildcard in AllowedDomains is valid.

**Fix.** Behavior `/api/analytics/*` ahead of `/api/*` with Managed-CachingDisabled, and
`cache-control: no-store` on every embed response. Catalog keeps its 5-minute cache.

**Exposure.** Acme data shown once to one Corvid user; embed bearer URLs of several tenants were
delivered to other tenants' browsers for about 3.5 hours but had already been redeemed. Notify both
Acme and Corvid; check CloudTrail for GenerateEmbedUrl volumes.
