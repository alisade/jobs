# Rubric: modernize/ai-c1 A guarded migration agent
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 60 | points = 60 * passed / total from grade.sh (1 visible test already passes) |
| 2 | Enforcement design | 20 | Full: all controls are in code at the tool boundary (allow-list for writes, deny-list for secrets, resolve-based containment, schema validation), denied writes never reach the reviewer, the system prompt is described as guidance not a control, errors are actionable for the model. Partial: works but relies on string checks that symlinks or normalisation defeat, or on the prompt. |
| 3 | Threat reasoning | 20 | Full: names the lethal trifecta (private data, untrusted content, an exfiltration channel) and which leg each control removes; CI hardening: ephemeral sandbox, no secrets mounted, no network egress except the model API, read-only checkout outside src/main, reviewer fatigue and diff size limits, evals with adversarial fixtures run on every prompt or tool change. Partial: generic "be careful with prompts". |
Total: 100
