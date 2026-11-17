# Rubric: awsfde/w4-c1 Tenant-scoped tool Lambda, single-table DynamoDB and LeadingKeys
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Tenant boundary in code | 15 | Full: one function reads the claim; no code path consults path/query/body tenant values except to log them; 404 for foreign items; key builders validate input. Partial: correct but tenant checks scattered or compared against supplied values. |
| 3 | Data model | 10 | Full: access patterns written down first, every table and GSI partition key tenant-prefixed, sensible sort keys for newest-first, no Scan-based pattern. Partial: works but a pattern needs a filter expression or Scan. |
| 4 | IAM depth | 15 | Full: explains ForAllValues vs ForAnyValue, that ForAllValues over an absent key evaluates true so Scan (no leading keys) must not be granted, index ARNs, session tag from AssumeRole, the tag-present guard. Partial: correct policy without the reasoning. Zero: StringEquals on a multivalued key or Scan granted. |
| 5 | ANSWER.md production thinking | 10 | Full: pool vs silo trade-off, assume-role latency and caching, Verified Permissions or Cedar for finer rules, CloudTrail and alarms, cross-tenant tests in CI. Partial: generic. |
Total: 100
