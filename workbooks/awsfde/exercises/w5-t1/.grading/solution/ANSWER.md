# ANSWER: awsfde/w5-t1 Acme's product shows a supplier it never used

## Approach

Ticket, then run/query.log (Acme rows carry tenant_id brightline-health), then run/load-jobs.log
and the CSVs in run/load/, then export.py.

## Root cause

export.py builds ids from each ERP's row numbers with no tenant prefix. Both tenants' files contain
sup-001, sup-002, part-100 and part-101. Ids are global to the graph, so Brightline's load on
2026-11-11 upserted Acme's vertices: load-jobs.log shows nodes_updated 4 with updated_node_ids
[sup-001, sup-002, part-100, part-101] and edges_replaced 2. Those vertices now have Brightline names
and tenant_id; the tool query constrains only the Product, so Acme's Penne path returns them and
Acme's own supplier names are gone. Brightline's smoke test passed because the merged vertices are
now Brightline's. The duplicates (CS-5480) are a missing DISTINCT, unrelated to the leak.

## Fix

Tenant-prefixed node and relationship ids; validate_load rejects collisions, cross-tenant or unknown
endpoints, duplicates and wrong-tenant rows; the query scopes every node and uses DISTINCT. make
replay: both loads complete with nodes_updated 0; Acme Penne -> Golden Grain Mills, Pacific
Packaging; Marinara -> Pacific Packaging, Sierra Farms; Brightline unchanged.

## Trade-offs / what I would do in production

Disable the graph tool, rebuild the graph and reload both tenants with prefixed ids. Exposure: Acme
saw Brightline supplier names; Brightline's parts link to Acme products; Acme lost data. Notify both.
Add the validator to the pipeline, cross-tenant tests in CI, an alarm on cross-tenant updates, and
evaluate one graph per tenant.
