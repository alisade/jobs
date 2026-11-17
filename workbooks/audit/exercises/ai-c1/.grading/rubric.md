# Rubric: audit/ai-c1 GRC MCP server: scoped read tools and a reviewer-gated write
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Tool design for a model | 15 | Full: task-shaped tools, descriptions that say what comes back and how to page, ToolError messages that name the fix (valid ids, which parameter), read/write annotations. Partial: correct but terse, or errors that only say "invalid". |
| 3 | Gate as a security control | 20 | Full: the write is authorized by a server-verified HMAC token bound to engagement, control, sample, reviewer and expiry; constant-time compare; SoD on preparer; nothing written on rejection; ANSWER.md explains why prompt rules or annotations are not controls (injection, any host can call the tool). Partial: checks present, reasoning thin. |
| 4 | Production thinking | 15 | Full: remote transport with OAuth per the MCP auth spec, key in Key Vault with rotation (key id in the token), short lifetimes and single-use (replay) tracking, per-call audit log with caller, arguments and result. Partial: one or two of these. |
Total: 100
