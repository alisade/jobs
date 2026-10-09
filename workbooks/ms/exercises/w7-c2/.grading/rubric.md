# Rubric: ms/w7-c2 Contoso Parts custom connector
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated checks | 50 | points = 50 * passed / total from grade.sh |
| 2 | Authentication design | 15 | Full: Entra ID (aad) identity provider with the Function's App ID URI as resource, accessCode oauth2 security definition, no secret in source, explains Easy Auth / token validation on the Function and per-connector redirect URI registration. Partial: aad configured but reasoning thin or secret handling unaddressed. Zero: function key or generic oauth2 kept. |
| 3 | Maker and agent experience | 15 | Full: clear summaries and sentence descriptions, internal helper operations, dynamic dropdowns that resolve, advanced vs important visibility chosen deliberately, descriptions good enough for Copilot Studio to pick the right tool. Partial: valid but noisy or copy-pasted strings. Zero: raw API names. |
| 4 | Paging and policy | 10 | Full: x-ms-pageable with nextLinkName matching the schema, setheader policy on Request with override; understands that makers must turn on Pagination in flows. Partial: one of the two. |
| 5 | ANSWER.md trade-offs | 10 | Full: ALM (connector in a solution, environment variables for host and settings, connection references), 429 behaviour with Retry-After, custom code vs policy templates, certification constraints. Partial: generic. Zero: empty. |
Total: 100
