# Rubric: backend/ai-c1 Tenant-scoped MCP tool server with an audit log
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Identity and scoping design | 15 | Full: identity verified once per session from the token (signature, constant-time compare, expiry, claims), never read from arguments; cross-tenant ids indistinguishable from missing ids; scoping in shared helpers rather than copy-pasted per tool. Partial: works but tenant checks scattered or inconsistent. |
| 3 | Writes and approvals | 10 | Full: crm.write enforced, idempotency key scoped to tenant and user with payload mismatch detection, proposal starts an approval with a deterministic key and never assigns; reasons stated. Partial: idempotent but keyed globally, or proposal key random. |
| 4 | Audit | 10 | Full: exactly one entry per call through one code path, outcome mapped from typed errors, args hash instead of raw arguments, fresh trace id, denials audited. Partial: entries missing on some error paths. |
| 5 | Tool and error design for a model | 10 | Full: descriptions say what, limits, side effects (propose does not assign) and that record content is untrusted; error messages are actionable (which scope, valid values). Partial: terse descriptions. |
| 6 | ANSWER.md | 10 | Full: concrete production plan: token exchange, RLS behind the tools, idempotency state in the service, quotas and kill switch, audit storage and access, evals on tool use. Partial: generic. |
Total: 100
