# Rubric: connect/x-2 The assistant refuses password resets after the security fix
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: guardrail version 3 added a denied topic ("Credentials and account access") whose definition and sample phrases describe ordinary self-service ("any request about passwords...", "my password", "unlock my account"); the input assessment blocks those turns before the model runs, so the assistant returns blockedInputMessaging and the Lambda hands off. Partial (10-15): "the guardrail blocks it" without the topic mechanism. Zero: blames the prompt or the model. |
| 3 | Evidence | 20 | Full: invocation log excerpts with stopReason guardrail_intervened, usage.inputTokens 0 (the model was never called, so the prompt cannot be the cause) and trace inputAssessment topicPolicy "Credentials and account access" BLOCKED; config lines; metrics drop on 2026-10-01; make evals before/after numbers. Partial: one piece. |
| 4 | Red herrings handled | 5 | Prompt line ruled out (zero tokens, input assessment); {USERNAME} explained as output ANONYMIZE of the USERNAME PII entity (working as configured, not a failure), and why it also reports guardrail_intervened. |
| 5 | Fix quality | 10 | Topic(s) narrowed to third-party credentials / account takeover / verification bypass with specific sample phrases, attacks still blocked, held-out cases pass, limits and name pattern respected, prompt-attack and PASSWORD protections intact, new version pinned in the Lambda (not DRAFT). No deleting the topic, no examples copied from the eval inputs to game it. |
| 6 | Prevention / production | 10 | Concrete: eval gate (legit + red-team sets, with held-out) before publishing a guardrail version; canary the version via config; alarm on handoff_reason_guardrail rate; review sample phrases with security; ApplyGuardrail-based offline evals against the real classifier; note the local stand-in only approximates the classifier. Partial: generic. |
Total: 100
