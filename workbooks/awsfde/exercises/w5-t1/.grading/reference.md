# Reference: awsfde/w5-t1

**Root cause.** `export_job.export.node_id` builds `sup-001`, `part-100` from each ERP's own row
numbers. Acme's and Brightline's ERPs both number suppliers from 1 and parts from 100. Node ids are
global to the graph (the docs: node IDs should be unique across all node files in the current and
previous loads), so the 2026-11-11 Brightline load matched four existing Acme vertices and upserted
them: names and `tenant_id` overwritten, Brightline's relationships attached. The tool query only
constrains the Product node, so Acme's Penne path now runs through vertices named after Brightline
suppliers. Acme's real supplier names are gone because those vertices were overwritten.

**Evidence.** `run/load/*-nodes.csv`: the same `sup-001`, `sup-002`, `part-100`, `part-101` in both
files. `run/load-jobs.log`: Brightline's job `nodes_updated: 4`, `updated_node_ids` lists exactly
those, `edges_replaced: 2`. `run/query.log`: Acme rows with `brightline-health` tenant_id.
Brightline's smoke test passed because the merged vertices now carry Brightline's names and tenant.

**Red herring.** CS-5480 duplicates: the query has no DISTINCT and Marinara uses two parts from the
same supplier. Adding DISTINCT does not remove the foreign suppliers.

**Fix.** Tenant-prefixed ids (`acme-foods:sup-001`) for nodes and relationships; `validate_load`
rejects ids that collide with another tenant's vertices, cross-tenant or unknown endpoints, duplicate
ids and wrong-tenant rows; the tool query scopes every node and uses DISTINCT.

**Repair and exposure.** The live graph is corrupted: stop the graph tool, rebuild the graph (or
delete the merged vertices and their relationships) and reload both tenants with prefixed ids.
Acme saw Brightline supplier names; Brightline's parts now connect to Acme products, so Brightline
users could reach Acme product names; Acme lost its supplier names in the graph. Notify both.

**Prevention.** Validator in the load pipeline, cross-tenant query tests in CI, an alarm when a load
updates vertices of another tenant, and a decision on per-tenant graphs (stronger isolation, more
cost) versus disciplined scoping in a shared graph.
