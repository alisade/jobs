# ANSWER: healthai/w6-t1 Member names in exported spans, with redaction switched on

## Approach

`make scan`: 10/610 log lines and 10/300 spans (3.3%) leak. Every leaking record is the WARNING
"eligibility retry for <name> member <id>"; the INFO "assessing case" lines that also contain names are
clean.

## Root cause

`RedactFilter` redacts `record.msg`, which for `%`-style calls is the template. The retry path in
`app/pipeline.py` passes the name and member id as args, merged by `getMessage()` after the filter ran,
in both the JSON sink and the span-event bridge. The f-string lines were clean because the values were
already in `msg`. The exporter's nested-attribute TODO is a red herring: the leaking spans carry the
identifiers in events, and their attributes are already scrubbed.

## Fix

The filter now redacts `record.getMessage()`, clears `args`, and redacts exception text and string
extras. Scanner after the fix: 0 lines, 0 spans; tests cover args, mapping args, f-strings, extras and
exceptions.

## Trade-offs / what I would do in production

Exposure: names and member ids of the ~3% of cases that hit the retry path since 2026.10, sent to a
vendor outside the BAA; Privacy runs the breach risk assessment and asks the vendor to delete the data.
Prevention: canary-identifier tests for each logging change, an allow-listed structured log schema, and
Sensitive Data Protection or a collector processor on the export path.
