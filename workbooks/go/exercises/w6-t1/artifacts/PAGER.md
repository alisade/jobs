# PagerDuty: PD-88213 [P2] kb-retriever search_kb p99 latency SLO burn

Triggered: 2026-10-06 14:02 UTC  Service: kb-retriever (prod, EKS cluster prod-use1-a)
Alert: `slo:search_kb_latency:p99 > 1s for 15m` (burn rate 14.4x, 1h window)

> From #support-agents, Priya (Agent Platform):
> Since about 13:30 the support agent mostly answers "I couldn't find anything in the
> knowledge base". Traces show the search_kb MCP tool taking 8-9 s and then failing.
> Nothing was deployed today. The only change I know of is that Tessa's team finished
> backfilling the Zendesk macros + Confluence export into the shared KB this morning
> (we went from ~640k chunks to ~2.1M). Also, unrelated maybe, a couple of weeks ago
> support said answers felt "less relevant" for a few tenants, ticket KB-224.

> From #db-oncall, Marcus:
> RDS CPU on kb-prod-pg went from 20% to 96% at 13:28. Connection pool for
> kb-retriever is pinned at max. KB-231 suggests raising hnsw.ef_search and the pool
> size; want me to bump max_conns to 50?

Runbook: https://wiki.harborpoint.example/runbooks/kb-retriever (statement_timeout on role
kb_reader is 3s; the MCP tool timeout is 10s)
