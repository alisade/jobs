# ANSWER: awsfde/w6-t1 Blank embedded dashboards and a cross-tenant view

## Approach

Read the tickets, then compared page loads with Lambda invocations: 64 embed requests at the edge but
only 11 Lambda runs. The edge log shows Hit for most embed requests, for every tenant.

## Root cause

The /api/* behavior uses tw-api-short-cache (DefaultTTL 300, query strings in the key, no identity in
the key). The Lambda sends no Cache-Control, so CloudFront caches the embed response for 300 s and
serves the same single-use URL to everyone. Redeem log: 53 already_used (blank dashboards). At
09:45:34 Acme load-063 missed and got a new Acme URL; Corvid load-064 hit 0.1 s later and its browser
redeemed first, so Corvid saw Acme's data and Acme got already_used.

## Fix

Added a /api/analytics/* behavior before /api/* using Managed-CachingDisabled
(4135ea2d-6df8-44a3-9df3-4b5a84be39ad) and cache-control: no-store on every Lambda response. make
replay: 0 blank, 0 cross-tenant, no Hit on the embed path; catalog and assets still cached.

## Trade-offs / what I would do in production

Exposure: Acme data shown once to one Corvid user; other tenants' already-used bearer URLs handed out
for about 3.5 hours. Red herrings: the 15-minute session (ASK-380, intended) and the valid
AllowedDomains wildcard. Prevention: no-store default in the API layer, review rule for cache
behaviors over authenticated paths, post-deploy two-tenant synthetic test, alarm on URLs issued vs
page loads.
