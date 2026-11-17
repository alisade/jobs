# ANSWER: audit/w2-c1 CM-03 population and sample

## Approach

The population comes from DeployHub's deploy log, the record that proves a change reached production.
It is defined as distinct change ids with a succeeded or rolled_back prod deployment, using the local
date in America/Chicago. PR and ticket data are joined to it; they do not filter it.

## Fix

Implemented the population, the reconciliation, five accuracy checks, the table lookup, seeded
selection over the population sorted by change_id, the hash and the log. I tested both period
boundaries in local time, re-deploys, failed and staging runs, and the unmerged/off-main changes.

## Trade-offs / what I would do in production

IPE: the control total report's parameters, run time (2026-10-05 14:02 CDT) and runner are documented.
The reconciliation (220 = 220) and the accuracy checks go in the workpaper, and the query is kept so
the auditor can re-run it. CM-03 is recurring, so the sample is 25 (40 if high risk). The three findings
are carried forward: the two unmerged changes and the missing ticket go to the control owner as likely
exceptions, even if the random sample does not select them. No model touches this step, because it
must be exactly reproducible.
