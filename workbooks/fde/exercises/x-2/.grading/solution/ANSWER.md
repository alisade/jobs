# ANSWER: fde/x-2 PII in decision logs

## Approach

Ran `make setup` and read `run/dlp-report.txt`: every finding is on `trust.decisions` or
`trust.risk`, none on `trust`. In `run/decisions.log` the `trust` lifecycle line is
redacted (`by [email]`) while the decision lines are not, so the regexes work and the
filter simply is not running for the child loggers. Then read `logging_setup.py` and
reproduced the logging rule in isolation.

## Root cause

`configure()` attaches `RedactingFilter` to the `trust` logger, not to its handler.
Logger filters run only for records logged on that exact logger (`Logger.handle`).
A record from `trust.decisions` propagates via `callHandlers()` straight to the `trust`
logger's handlers and never passes the `trust` logger's filters; only handler filters run
for propagated records. PR #412 moved decision and risk logging onto child loggers
(`getLogger("trust.decisions")`, `getLogger("trust.risk")`), so redaction silently stopped
for exactly those lines.

```
$ cat run/dlp-report.txt
  CARD_BIN_FIELD  logger=trust.decisions    lines=24
  EMAIL           logger=trust.decisions    lines=24
  EMAIL           logger=trust.risk         lines=3
  PAN             logger=trust.risk         lines=3
$ head -2 run/decisions.log
{"logger": "trust", "msg": "trust layer started for northwind-prod-use1 by [email]"}
{"logger": "trust.decisions", "msg": "decision allow hook=checkout customer=j.chen@example.org",
 "decision": {..., "card_bin": "552233"}}
```

Repro: a handler on logger `p` with a deny-all filter on `p`: `getLogger("p.c").warning()`
is written, `p.warning()` is dropped.

Not the cause: `customer_email` is `Field(exclude=True)` and is absent from every
`decision` payload; the email comes from the `%s` argument in the message.

## Fix

`trustlog/logging_setup.py`: `handler.addFilter(RedactingFilter())` instead of
`trust.addFilter(...)`. Verified: `make test` green, `make scan` -> "no findings".

## Trade-offs / what I would do in production

- Stop interpolating the email: log a salted digest; redaction stays as defense in depth.
- CI test that drives every logging call site and runs the DLP rules over the output.
- Purge `agent-trust` from 2026-10-07 15:42, fields `msg` and `decision.card_bin`, loggers
  `trust.decisions` / `trust.risk`; report under DH-7 / PCI DSS 3.4.
