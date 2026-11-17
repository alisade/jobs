# Rubric: healthai/w6-t1 Member names in exported spans, with redaction switched on
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause and evidence | 35 | Full: `RedactFilter.filter` redacts `record.msg`, the format template, before `msg % args` is merged by `getMessage()`; the 2026.10 retry path logs the name and member id as `%s` args, so those values pass untouched into the JSON sink and, through the span-event bridge, into ~3.3% of spans (10/300). f-string lines are clean because the values are already inside `msg`. Quotes leaking sample records. Partial: "args" without the mechanism or numbers. Zero: blames the exporter. |
| 3 | Red herring ruled out | 15 | Shows the leaking spans carry identifiers in `events`, not attributes; attributes like `khp.member` are already `[MEMBER]`; no nested attributes exist, so the TODO cannot explain it. |
| 4 | Fix, exposure and prevention | 20 | Filter redacts `getMessage()` and clears args, plus extras and exception text. Exposure: which cases and fields since the retry path shipped, vendor outside the BAA, Privacy's breach risk assessment (45 CFR 164.402). Prevention: canary-name tests on every logging change, structured logging with an allow-list of fields, SDP or a collector processor on export. |
Total: 100
