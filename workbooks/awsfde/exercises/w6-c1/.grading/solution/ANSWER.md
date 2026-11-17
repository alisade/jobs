# ANSWER: awsfde/w6-c1 Embed-URL Lambda

## Approach

The tenant claim selects the tenant config; nothing from the query string except a dashboard id,
which is checked against that tenant's list. Registered tenants get a user ARN in their own
namespace; anonymous tenants get only their dashboard ARNs and a tenant_id session tag.

## Fix

Implemented validation, build_request and handler with error mapping and no-store headers.

## Trade-offs / what I would do in production

The URL is single use and valid 5 minutes; the session lasts SessionLifetimeInMinutes (15-600), so
the app fetches a new URL per page load and nothing may cache it. RLS: a rules dataset per tenant
namespace for registered users; tag-based rules on tenant_id for anonymous. Provision readers on
first login with RegisterUser. Scope the Lambda role to the dashboard and user ARNs, alarm on
throttling, and keep URLs out of logs.
