# Rubric: go/w6-c1 Incident-triage agent loop with anthropic-sdk-go
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Loop correctness and tool-result protocol | 15 | Full: assistant turn replayed via `ToParam()`, all results of a turn in ONE user message in tool_use order with matching ids, every stop reason handled explicitly, budget checked before the call. Partial: works for the happy path but one result per message, or ordering depends on goroutine finish order. Zero: loop does not terminate or drops tool_use ids. |
| 3 | Concurrency done right | 10 | Full: bounded errgroup (`SetLimit`) or semaphore, results written to an index not appended under a race, per-call timeout context, panic recovered inside the goroutine, no shared mutable state on `Agent` between runs. Partial: unbounded goroutines or a mutex-guarded append that loses order. Zero: sequential, or data races. |
| 4 | Error design | 10 | Full: tool failures become is_error data (the model can recover) while API/ctx failures are returned wrapped with `%w`; typed `*MaxTurnsError` and sentinels usable with `errors.As/Is`; messages to the model are actionable (list tools, name missing fields). Partial: mixes the two classes. Zero: string errors, panics escape. |
| 5 | ANSWER.md and production judgement | 15 | Full: explains the design and 3+ concrete production points (token/cost budget per run, streaming for long answers, prompt caching of system+tools, retry/backoff on 429/529 via SDK options, OTel spans per turn and tool with GenAI semconv, Bedrock via Pod Identity, read-only tools and server-side enforcement against prompt injection). Partial: generic. Zero: empty. |
Total: 100
