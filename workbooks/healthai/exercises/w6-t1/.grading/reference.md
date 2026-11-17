# Reference: healthai/w6-t1

Root cause: `app/logsetup.py` `RedactFilter.filter` does `record.msg = redact(str(record.msg))`. For
`log.warning("eligibility retry for %s member %s", name, member)` the template has no identifiers; the
values sit in `record.args` and are merged later by `record.getMessage()` in the formatter and in the
span-event bridge. The retry path (added in 2026.10) runs for about 3% of cases: 10 of 610 log lines and
10 of 300 spans leak. The main path uses an f-string, so its values are already in `msg` and get
redacted, which is why most records were clean and the filter "seemed to work".

Red herring: `scrub_attributes` has a TODO for nested attributes, but the pipeline emits only flat
attributes and `khp.member` is already exported as `[MEMBER]`; the leaking text is in span events.

Fix: `.grading/solution/app/logsetup.py`: `record.msg = redact(record.getMessage()); record.args = None`,
plus exception text and string extras.
