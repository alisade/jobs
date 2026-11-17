# Rubric: genai/ai-c1 An MCP server for store associates
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Tool design | 15 | Names and descriptions say when to use each tool and how outputs chain (sku from find_product into store_stock/prepare_hold); compact outputs; errors tell the model what to do next. |
| 3 | Least privilege and data minimization | 15 | Write tools not registered without scope (not merely refused); store scope enforced server-side; indistinguishable not-found; no PII or internal cost fields; token args truncated in audit. |
| 4 | ANSWER.md | 20 | Full: transport choice, OAuth for a remote server with the store scope coming from the associate's token, rate limits, audit storage, how to eval tool selection (a small set of associate questions scored on tool choice and args), versioning descriptions. Partial: generic. |
Total: 100
