# Reference: healthai/w6-c1

See `.grading/solution/deid/core.py`.
- Names first (known names from the Patient resource, hyphen parts too), then member ids to keyed
  pseudonyms, then typed patterns, then ages over 89. Ordering matters: redact names before generic
  patterns so "Okafor-Benn" does not survive as "Benn".
- The logging filter calls `record.getMessage()` (msg % args), stores the redacted string in `msg` and
  sets `args = None`; formats and redacts `exc_info` into `exc_text`; redacts non-standard attributes
  (`extra=`). A filter that only touches `record.msg` leaks every value passed as an argument (w6-t1).
- `minimum_necessary` is the real control: identifiers never enter the prompt, so redaction is the
  second line of defence, not the only one.
- Limits: regexes cannot find names you do not know (a neighbour's name in a note). In production run
  Sensitive Data Protection inspection (PERSON_NAME and friends) or the Healthcare API de-identify
  operation for data sets, and keep exports to BAA-covered services where possible.
