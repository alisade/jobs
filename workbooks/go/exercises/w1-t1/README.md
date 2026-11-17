# go/w1-t1 flagd returns 500 on every flag update

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Week 1:** Go language and idioms (Wed interfaces, Thu errors)

## Scenario

Corvid Pay runs `flagd`, a small Go feature-flag service, on EKS (two replicas behind a
ClusterIP Service). Product teams change flags through the admin UI, which calls
`PUT /v1/flags/{key}`. Reads by the payment services are unaffected.

## Symptoms (as paged)

> **PagerDuty, 2026-10-06 14:16 UTC, sev2, #inc-flagd**
> "Since about 14:00 nobody can change a feature flag. The admin UI shows 'Internal error'
> for every save, even for flags we have edited a hundred times. We need to ramp
> `checkout-v2` from 10% to 50% before the 16:00 campaign. Reads look fine. Rolling back
> is the last resort: v1.14.0 also carries the multi-field validation that Product wants
> for the campaign."

What on-call collected is in `artifacts/`:

- `flagd-prod.log` - JSON logs from both pods after the deploy
- `curl-transcript.txt` - requests made from a debug pod
- `git-log.txt` - what changed in v1.14.0
- `grafana-flagd.txt` - response codes by route around the deploy marker

## Task

1. Find the root cause. Reproduce it locally (`make test`, `make run` + `make repro`).
2. Fix it in the code with the smallest correct change. Keep the v1.14.0 features: all
   invalid fields reported at once, and empty descriptions omitted from JSON.
3. Explain it in `ANSWER.md`. The explanation matters more than the patch: a reviewer
   should understand **why** a function that "returns nil" made `err != nil` true.

## Acceptance criteria

- A valid `PUT` returns 200 and the flag is stored; an invalid `PUT` returns 422 with every
  invalid field in `fields`.
- `Service.Put` returns an untyped `nil` on success, and `errors.As` still finds a non-nil
  `*ValidationError` through wrapping on failure.
- No regressions on GET, LIST, DELETE, bad JSON or key mismatch.
- `ANSWER.md` names the root cause precisely, with evidence (commands and output).

## How to run

```
make setup     # build bin/flagd (v1.14.0), list artifacts
make test      # visible tests; one fails with the symptom
make run       # flagd on 127.0.0.1:8088 (debug logs)
make repro     # in a second terminal: the on-call requests
```

## What to submit

Your code change and a completed `ANSWER.md` (Approach, Root cause with evidence, Fix,
Trade-offs). Then `/grade go/w1-t1` from the workbooks root.

## Study-guide links

- Effective Go, interfaces and other types: https://go.dev/doc/effective_go#interfaces_and_types
- Working with Errors in Go 1.13: https://go.dev/blog/go1.13-errors
- Go Code Review Comments: https://go.dev/wiki/CodeReviewComments
- 100 Go Mistakes (#45 returning a nil receiver): https://100go.co/
