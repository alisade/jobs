# Rubric: go/w1-c1 Port snapshot-janitor from Python to idiomatic Go
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Error handling idioms | 15 | Full: `errors.As` into `smithy.APIError` for codes, `%w` wrapping, `errors.Join` with the sentinel, no string matching on messages, no swallowed errors. Partial: works but matches on `err.Error()` or loses the underlying errors. Zero: panics or ignores errors. |
| 3 | Idiomatic Go structure | 10 | Full: small interface consumed not defined by AWS types, zero-value-friendly config (`cmp.Or` defaults), `aws.ToString`/`aws.ToTime` for nil safety, early returns, no global state. Partial: works but Python-shaped (deep nesting, flags parsed inside the package). Zero: copy of the Python control flow with `interface{}` everywhere. |
| 4 | main.go operability | 10 | Full: flags match the Python script, JSON slog, `signal.NotifyContext` for SIGTERM, exit codes 0/1/2 via `errors.Is`, `os.Exit` only at the top. Partial: some missing. Zero: still the TODO. |
| 5 | ANSWER.md and production judgement | 15 | Full: explains behaviours kept/changed vs Python (e.g. failure exit code, cap semantics), plus 2-3 concrete production points (least-privilege IAM with `ec2:DeleteSnapshot` conditioned on owner/tag, CronJob `concurrencyPolicy: Forbid`, metrics/alerting on failures, throttling/retry config). Partial: generic. Zero: empty. |
Total: 100
