# KB-224: "Answers feel less relevant" (opened 2026-09-25 by support ops)

Since roughly the 24th, a few tenants report the agent says it could not find an article
that definitely exists. Example: acme, "how do I rotate the SSO signing cert" -> 0 hits
with min_similarity 0.72. The article is in the KB (doc_id confluence-sso-rotate).

Spot check by Devon on 2026-09-26: running the search with min_similarity 0.0 returns the
right article in position 1, but with similarity 0.31. Lowering the agent default to 0.3
"fixes" it. Parked as a tuning issue.
