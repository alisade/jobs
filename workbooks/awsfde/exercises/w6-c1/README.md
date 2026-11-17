# awsfde/w6-c1 - Embed-URL Lambda: registered and anonymous embedding

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 6 (Wed: registered vs anonymous embedding; Thu: GenerateEmbedUrl APIs, allowed domains and session lifecycle; Fri: the backend that mints URLs)

## Scenario

Tidewater Ask shows each customer an operations dashboard built in Quick Sight (formerly Amazon
QuickSight; the API is still `quicksight`). Two commercial models exist:

- **Registered** tenants (Acme Foods, Corvid Logistics) have named Quick Sight readers, one
  namespace per tenant, and user-based row-level security.
- **Anonymous** tenants (Brightline Health, Delta Outfitters) share dashboards on capacity pricing;
  rows are restricted by tag-based RLS on a `tenant_id` session tag.

The web app calls `GET /analytics/embed-url` through an HTTP API with a Cognito JWT authorizer, then
hands the URL to the Embedding SDK. You write the Lambda. The account team has collected the
support tickets from the pilot: "domain not allowed", "user not found", throttling at 09:00, and a
security reviewer who found an embed URL in a log group.

The docs rules you design around (GenerateEmbedUrl API reference): the URL contains a temporary
bearer token, is valid for 5 minutes and cannot be re-used once redeemed; the session it opens lasts
`SessionLifetimeInMinutes` (15 to 600, default 10 hours); `AllowedDomains` overrides the console's
domain list for that call, takes up to three domains, and `https://*.example.com` covers subdomains.

## What you have

| Path | What it is |
|---|---|
| `embed/tenants.json` | account, region, allowed domains, session lifetime, per-tenant mode and dashboards |
| `embed/handler.py` | `validate_domains`, `validate_lifetime`, `build_request`, `handler` - **your work**; `load_config`, `ERRORS` and helpers are done |
| `tests/` | a real `quicksight` client with a botocore `Stubber` (requests are validated against the real API model) |

## Your task

1. `validate_domains()` and `validate_lifetime()`: reject anything the API would reject or that is
   unsafe (not https, a path or trailing slash, more than three, a lifetime outside 15-600 or not an
   integer). `load_config()` calls them, so a bad deploy fails at cold start, not per user.
2. `build_request(cfg, claims, requested_dashboard)` returns `(operation, kwargs)`:
   - tenant from the `tenant_id` claim only (403 if missing or not configured);
   - registered: `UserArn` `arn:aws:quicksight:<region>:<account>:user/<tenant namespace>/<username claim>`
     (validate the user name; 403 if unusable), the tenant's dashboard as `InitialDashboardId`, any
     other requested dashboard is a 404;
   - anonymous: `Namespace: "default"`, `AuthorizedResourceArns` = the tenant's dashboard ARNs only,
     `SessionTags` `[{"Key": "tenant_id", "Value": <tenant>}]`, the requested dashboard if it is one of
     the tenant's (else 404), otherwise the first;
   - both: `AwsAccountId`, `SessionLifetimeInMinutes`, `AllowedDomains` from config.
3. `handler()`: call the operation, return `{"embedUrl": ...}`; map errors with `ERRORS`
   (`QuickSightUserNotFoundException` becomes an actionable 403), `ThrottlingException` to 503 with
   `retry-after`; `cache-control: no-store` on every response; never log the URL.
4. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Requests for both modes match the API model and carry exactly the tenant's scope (namespace, ARNs, tag).
- A tenant value in the query string, another tenant's dashboard, or a bad user name never widens access.
- Error mapping, retry-after, no-store and no URL in logs.
- Domain and lifetime validation match the API rules.
- `ANSWER.md` covers the session lifecycle and the RLS model for each mode.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/w6-c1
make clean
```
