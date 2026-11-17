# awsfde/w5-c1 - Supply-chain graph: openCypher queries and a tenant-safe graph tool

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Mon: graph modeling; Tue: openCypher; Wed: Neptune Database vs Neptune Analytics; Thu: a graph tool for the agent)

## Scenario

Acme Foods keeps asking Tidewater Ask relationship questions that vector search answers badly:
"which suppliers does Marinara depend on?", "if Pacific Packaging's Tijuana plant goes down, which
customers are exposed?". The platform loads each tenant's supply chain into one shared Neptune
Analytics graph, every vertex carrying a `tenant_id` property. You write the openCypher queries and
the agent tool that runs them, and you make the tool safe for a multi-tenant graph: the model chooses
a question, never the query text, and the tenant comes from the verified token.

## What you have

| Path | What it is |
|---|---|
| `graph/nodes.csv`, `graph/edges.csv` | two tenants' graphs in the Neptune openCypher load format (`:ID`, `:LABEL`, `:START_ID`, `:END_ID`, `:TYPE`, `name:String`, `lead_days:Int`) |
| `graphlib/loader.py` | loads those files into a networkx `MultiDiGraph` (done) |
| `graphlib/cypher.py` | `read_query()`, `run(graph, query, params)`: binds `$parameters` and runs the query with grand-cypher, a local openCypher engine (done) |
| `queries/q1..q5*.cypher` | **your work**: one query each; the header comments define parameters and output |
| `graphlib/graph_tool.py` | **your work**: `check_tenant_scoped()`, `build_request()`, `run_tool()` for `neptune-graph` `ExecuteQuery` |
| `tests/` | visible tests; the tool tests use a real `neptune-graph` client with a botocore `Stubber` |

Model: `(:Supplier)-[:SUPPLIES]->(:Part)-[:USED_IN]->(:Product)<-[:ORDERED]-(:Customer)`, and
`(:Supplier)-[:LOCATED_IN]->(:Facility)`. Both tenants have a supplier named "Pacific Packaging"
and a customer named "Hillside Markets", on purpose.

## Your task

1. Write the five queries. q1 and q2 are multi-hop, q3 uses a variable-length relationship
   (`-[*1..2]->`), q4 aggregates. Every node pattern in every query is constrained to
   `$tenant_id`, either in its property map (`{tenant_id: $tenant_id}`) or in `WHERE`
   (`s.tenant_id = $tenant_id`). The q1 draft works on a one-tenant graph; fix it.
2. `check_tenant_scoped(query)`: raise `ValueError` naming any node variable that is not
   constrained to `$tenant_id`; an anonymous node `()` is never scoped.
3. `build_request(graph_id, ctx, tool, args)`: only template names from `TEMPLATES`, only their
   declared arguments (each a string matching its pattern), `$tenant_id` bound from `ctx`, the
   template checked with `check_tenant_scoped()`, `language: OPEN_CYPHER`,
   `queryTimeoutMilliseconds`. Anything else raises `ToolError` (including a `query` or
   `tenant_id` argument from the model).
4. `run_tool()`: call `execute_query`, parse the streaming JSON payload `{"results": [...]}`,
   return at most `MAX_ROWS` rows and a `truncated` flag.
5. Fill in `ANSWER.md`.

### How the queries run on Neptune Analytics

The same text, with parameters bound by the service (AWS CLI shown; the tool does this with boto3):

```bash
aws neptune-graph execute-query --graph-identifier g-tw0graph01 --language OPEN_CYPHER \
  --query-string 'MATCH (s:Supplier {tenant_id: $tenant_id})-[:SUPPLIES]->(p:Part {tenant_id: $tenant_id})
                  -[:USED_IN]->(x:Product {tenant_id: $tenant_id, name: $product})
                  RETURN DISTINCT s.name ORDER BY s.name' \
  --parameters '{"tenant_id": "acme-foods", "product": "Marinara 680g"}' out.json
```

### Local engine notes (grand-cypher)

grand-cypher implements a subset of openCypher. Write standard openCypher that also runs here:
use `RETURN DISTINCT n.prop` without an alias when you need DISTINCT, write aggregates in upper
case (`COUNT(p)`), and prefer property maps or `AND`-joined `WHERE` clauses. Tests compare rows
by position, so column names do not matter. On Neptune you could also constrain the intermediate
nodes of a variable-length path (`ALL(n IN nodes(path) WHERE n.tenant_id = $tenant_id)`); the
local engine cannot, so q3 constrains its two named nodes.

## Acceptance criteria (what the grader checks)

- Each query returns the expected rows for both tenants and several parameter values.
- Results stay correct when cross-tenant relationships are planted in the graph (bad data must not
  leak through any query).
- `check_tenant_scoped()` passes your queries and rejects unscoped, anonymous and literal-tenant patterns.
- The tool rejects unknown tools, model-supplied query text, a model-supplied `tenant_id`, extra or
  invalid arguments; binds the tenant from context; sends a valid `ExecuteQuery` request; truncates.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/w5-c1
make clean
```
