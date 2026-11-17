# KB-231: Tune pgvector for larger KB (opened 2026-09-30 by Marcus, db-oncall)

With the Zendesk/Confluence backfill coming we should get ahead of it:

1. Raise `hnsw.ef_search` from 40 to 200 on the kb_reader role. Better recall on big
   indexes, and the pgvector docs say it is the knob for recall vs speed.
2. Raise kb-retriever pgxpool `max_conns` 10 -> 50 and RDS max_connections accordingly,
   since we already see acquire waits at peak.
3. Consider `SET hnsw.iterative_scan = relaxed_order` so filtered queries return k rows.

Status: Open. Not started.
