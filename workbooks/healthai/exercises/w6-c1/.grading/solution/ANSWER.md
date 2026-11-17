# ANSWER: healthai/w6-c1 PHI de-identification for logs, prompts and traces

## Approach

Minimum necessary first: the criteria step gets a member token, age band, sex, codes, medications,
observations, the service and redacted notes; nothing else. Then `redact_text` in a fixed order (known
names, member id pseudonyms, typed patterns, ages over 89). The logging filter redacts the formatted
message, exception text and extras; spans are scrubbed on export.

## Fix

The draft only caught SSN and email, used an unkeyed hash, forwarded the whole Patient into the prompt
and redacted `record.msg` before args. Tests plant every identifier type in several formats and check
handler output, prompts, context and span attributes, plus a precision test for clinical content.

## Trade-offs / what I would do in production

Regexes miss names we do not know; use Sensitive Data Protection inspection on free text and the
Healthcare API de-identify operation for eval sets. A keyed pseudonym is still PHI for anyone who can
reach the key; keep the key in Secret Manager outside the recipient's project. Checkpoints, vector index
metadata and eval files are PHI stores too. Run canary-identifier tests in CI on every logging change.
