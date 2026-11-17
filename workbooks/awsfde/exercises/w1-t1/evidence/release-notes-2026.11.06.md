# tidewater-ask-answer release 2026.11.06 (deployed Fri 2026-11-06 16:20)

Theme: resilience hardening after INC-4410 ("Ask shows errors at 09:00 on Mondays").

- Bedrock client: more SDK retries for throttling (`max_attempts` 2 -> 10, standard mode).
- New `answer_svc/resilience.py`: `call_with_retries` with an app-level `RetryPolicy`
  (5 attempts, 1 s between attempts) so a transient error never reaches the user.
- `service.answer` now goes through `call_with_retries`.
- Lambda reserved concurrency 100 -> 150 to absorb Brightline Health growth (two new clinics).
- Unit tests: `call_with_retries` returns on the 3rd attempt when the first two throw.

Rollout: canary 10% for 30 min on Friday afternoon (low traffic), no alarms, then 100%.
Reviewed-by: platform team.
