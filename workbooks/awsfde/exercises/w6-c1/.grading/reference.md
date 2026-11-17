# Reference: awsfde/w6-c1

Solution: `.grading/solution/embed/handler.py`.

- Registered mode: `GenerateEmbedUrlForRegisteredUser` with
  `arn:aws:quicksight:<region>:<account>:user/<namespace>/<user>`; the user's permissions and
  user-based RLS apply. A missing user is `QuickSightUserNotFoundException`, which in practice means
  "not provisioned in that namespace": tell the admin, or register on first login.
- Anonymous mode: `GenerateEmbedUrlForAnonymousUser` in the `default` namespace, the tenant's
  dashboard ARNs only in `AuthorizedResourceArns`, and the `tenant_id` session tag that tag-based RLS
  rules match. Capacity pricing is required, otherwise `UnsupportedPricingPlanException`.
- Lifecycle (API reference): the URL holds a bearer token, is valid for 5 minutes and is single use;
  the session lasts `SessionLifetimeInMinutes` (15-600, default 600). So the frontend asks for a new
  URL on every page load, and nothing between the browser and this Lambda may cache the response
  (`cache-control: no-store`; see w6-t1 for what happens otherwise).
- `AllowedDomains`: up to three per call, overrides the console list, `https://*.domain` for subdomains.
