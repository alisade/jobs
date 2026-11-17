# Reference: fde/x-2 PII in decision logs

## Root cause

`configure()` attaches `RedactingFilter` to the `trust` logger (`trust.addFilter`). In
Python logging, a logger's filters are consulted only in `Logger.handle()` for records
created on that logger. A record created on `trust.decisions` is filtered by
`trust.decisions`' own filters, then `callHandlers()` walks up the hierarchy and hands it
to the `trust` logger's handlers directly; the `trust` logger's filters never see it.
Handler filters (`Handler.handle()` -> `self.filter(record)`) run for every record that
reaches the handler. Before PR #412 every call used `getLogger("trust")`, so the logger
filter ran; after it, decisions and risk failures log on child loggers and bypass it.

Evidence in the bundle: the `trust` lifecycle line reads `by [email]`, while every
`trust.decisions` line has a raw email in `msg` and a raw `card_bin`, and `trust.risk`
lines carry the PAN. The DLP report breaks down only by child logger.

Minimal repro:

```python
import logging, io
s = io.StringIO(); h = logging.StreamHandler(s)
p = logging.getLogger("p"); p.addHandler(h); p.addFilter(lambda r: False)
logging.getLogger("p.c").warning("child")   # written: parent filter skipped
p.warning("parent")                          # dropped
```

## Red herring

`customer_email` is `Field(exclude=True)` and that works: the `decision` payload never
contains it. The email in the leaked lines is the third `%s` argument interpolated into
the message, which the filter would have redacted had it run.

## Fix

`handler.addFilter(RedactingFilter())` in `configure()` (and drop the logger filter).
Every record the decisions.log handler writes is redacted, from any `trust.*` logger at
any depth, including ones that do not exist yet.

## Production

- Stop logging the email at all: log a salted digest; redaction is defense in depth, not
  the design.
- CI: a test that emits through every module and runs the DLP rules over the output.
- Scope and purge: index `agent-trust`, 2026-10-07 15:42 onward, fields `msg` and
  `decision.card_bin`, loggers `trust.decisions` and `trust.risk`; notify per DH-7 / PCI.
