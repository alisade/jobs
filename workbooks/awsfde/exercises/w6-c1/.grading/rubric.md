# Rubric: awsfde/w6-c1 Embed-URL Lambda: registered and anonymous embedding
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Tenant scoping | 15 | Full: tenant only from the claim; registered user ARN in the tenant namespace with a validated user name; anonymous AuthorizedResourceArns limited to the tenant and the session tag set; requested dashboards checked against the tenant's list. Partial: one mode scoped loosely (e.g. all dashboards authorized). |
| 3 | Failure handling | 10 | Full: config validated at load; user-not-found message tells the admin what to do; throttling retryable; no URL in logs; no-store everywhere. Partial: generic 500s. |
| 4 | Session lifecycle and RLS understanding (ANSWER.md) | 15 | Full: 5-minute single-use URL vs 15-600 minute session; fresh URL per page load and never cached; user-based RLS rules dataset vs tag-based rules for anonymous; namespaces per tenant; capacity pricing requirement. Partial: some. |
| 5 | Production thinking | 10 | Full: IAM scoped to ARNs, user provisioning on first login, quota/throttling at peak, CloudFront/API caching risk, monitoring. Partial: generic. |
Total: 100
