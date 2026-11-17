# ANSWER: awsfde/w6-c1 Embed-URL Lambda

## Approach

<!-- How the tenant scopes each mode (namespace, AuthorizedResourceArns, session tag) and why the
claim is the only source. -->

## Fix

<!-- What you implemented. -->

## Trade-offs / what I would do in production

<!-- URL vs session lifetime, and why the frontend must fetch a fresh URL per page load; how
user-based and tag-based RLS rules are maintained per tenant; registered user provisioning
(RegisterUser on first login); caching risks in front of this endpoint; quotas and throttling at
peak; IAM for the Lambda role (quicksight:GenerateEmbedUrlFor* scoped to dashboard and user ARNs). -->
