# Reference: awsfde/w5-c1

Reference queries: `.grading/solution/queries/`; tool: `.grading/solution/graphlib/graph_tool.py`.

- **Scope every node, not just the anchor.** On a shared graph, the q1 draft constrained only the
  product. Bad data or an id collision (see w5-t1) that links another tenant's supplier to your part
  would then surface in your answer. Constraining every node makes a cross-tenant path match nothing.
- **DISTINCT.** Multi-hop paths multiply rows (Pacific Packaging supplies two parts of Marinara).
- **Variable length.** `-[*1..2]->` must be bounded; an unbounded `*` on a dense or cyclic graph is
  the classic runaway query. On Neptune, add a path predicate for intermediate nodes as well.
- **The tool never accepts query text.** Templates are named, arguments are typed and pattern
  checked, `$tenant_id` comes from the verified context, and the template is checked for scoping
  before it is sent. `queryTimeoutMilliseconds` and a row cap bound cost and context size.
- **Parameters, not concatenation.** Parameters keep the plan cacheable and remove injection.

Production: one graph per tenant gives hard isolation but each Neptune Analytics graph has its own
memory-based capacity and cost; a shared graph needs scoping discipline like this tool's. Use IAM
(SigV4) auth and private endpoints; consider Neptune Database for transactional OLTP workloads and
Neptune Analytics for in-memory analytics, algorithms and vector similarity; for simple one-hop
lookups a DynamoDB adjacency list is cheaper.
