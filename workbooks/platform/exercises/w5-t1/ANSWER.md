# ANSWER: platform/w5-t1 The RIQ burn-rate alert never fired

## Approach

<!-- How you investigated: which queries you ran in which order, what you ruled out first. -->

## Root cause

<!-- The actual cause, with evidence: query output excerpts, the relevant lines of the rule file,
the scrape config before and after, the commit. Why did the rule evaluator log show no errors? -->

## Fix

<!-- What you changed in rules/riq-slo.rules.yaml and why; per-cluster or aggregated and why; the guard;
how you verified it (make alerts output on the incident data). -->

## Trade-offs / what I would do in production

<!-- Red herrings and how you ruled them out. Preventing a repeat: rule unit tests in CI (promtool test rules
style), a guard per SLO, label contract for PodMonitoring, alert on rule groups producing empty results,
synthetic burn tests, who owns SLO rules after a migration. -->
