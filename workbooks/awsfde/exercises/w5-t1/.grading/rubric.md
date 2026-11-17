# Rubric: awsfde/w5-t1 Acme's product shows a supplier it never used
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the export job builds node ids from each ERP's own sequence numbers (sup-001, part-100) with no tenant prefix; ids are global to the graph, so Brightline's load matched Acme's existing vertices and upserted them (names and tenant_id overwritten, Brightline relationships attached to Acme's parts); Acme's suppliers sup-001/sup-002 now carry Brightline names, and the tool query only constrains the product, so the mixed path is returned. Partial (10-15): "ids collided" without the shared-graph upsert or without why the query let it through. Zero: blames the model, DISTINCT or the loader. |
| 3 | Evidence | 20 | Full: run/load/ files with identical ids in both tenants' CSVs, load-jobs.log for 2026-11-11 with nodes_updated 4 and updated_node_ids [sup-001, sup-002, part-100, part-101] and edges_replaced 2, query.log rows with tenant_id brightline-health in Acme's answers, the docs line on unique node ids. Partial: one source. |
| 4 | Red herring handled | 5 | Duplicates are a separate missing DISTINCT (Pacific/Clearview supplies two parts of Marinara); fixing DISTINCT alone does not remove the foreign suppliers. |
| 5 | Fix quality | 10 | Full: tenant-prefixed node and relationship ids, validator checks collisions against the existing graph and cross-tenant endpoints and fails the load, every node in the tool query scoped plus DISTINCT. Partial: one or two of the three. Zero: a Brightline-specific rename. |
| 6 | Exposure, repair and prevention | 10 | Full: exposure both ways (Acme sees Brightline supplier names; Brightline's graph now links to Acme products, so Brightline queries over those parts can reach Acme data; Acme's own supplier names were overwritten, i.e. data loss), repair the live graph (stop answers, rebuild or delete the four merged vertices and their relationships, reload both tenants with prefixed ids, re-run evals), prevention (validator in the pipeline, a cross-tenant query suite in CI, consider one graph per tenant or ID spaces, alarm on nodes_updated by a different tenant). Partial: generic. |
Total: 100
