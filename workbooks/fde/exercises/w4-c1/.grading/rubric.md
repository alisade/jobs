# Rubric: fde/w4-c1 Customer MCP server: trust-advisor tools for merchant engineers
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Data protection | 15 | Full: results built field by field from an allowlist (no `**record`), digests for ids, notes redacted with patterns that keep decision ids, cap applied after redaction. Partial: works but by deny-listing keys off the raw record (fragile when the export grows a field). Zero: any raw identifier reachable. |
| 3 | Tool design for a model caller | 15 | Full: descriptions say when to use the tool and the input format; errors tell the caller how to fix the call; structured pydantic outputs; annotations complete. Partial: terse docstrings or generic errors. Zero: exceptions/tracebacks surface. |
| 4 | Safe handling of untrusted input | 10 | `yaml.safe_load`, size caps before parsing, id format check before lookup, module allowlist checked before `import_module` with a boundary-safe prefix match, broad import failures caught without leaking the exception text. |
| 5 | Code quality | 5 | Small helpers, typed, no duplication between tools, MRO logic readable. |
| 6 | ANSWER.md trade-offs | 10 | Full: explains that importing a module executes its code (so read-only tool, not side-effect-free), proposes auth (OAuth/JWT with per-merchant audience or tenant claim, store scoped by merchant), and at least one more concern (regex redaction limits, rate limiting, audit logging). Partial: generic. Zero: empty. |
Total: 100
