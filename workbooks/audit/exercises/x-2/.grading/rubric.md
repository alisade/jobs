# Rubric: audit/x-2 ControlPilot production architecture and control-owner review pack
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Execution model and review checkpoints | 15 | Full: durable orchestration (Durable Functions or an equivalent with persisted checkpoints) per run and per sample, pauses for days at a review gate, idempotency keys on GRC/blob writes, preparer != reviewer enforced in code, 10% pass re-review sampling, a kill switch that actually stops work within 15 min (feature flag + revoked role or disabled orchestrations). Partial: "human in the loop" without mechanics. |
| 3 | Identity and tool scoping | 15 | Full: user-assigned managed identity, Workload Identity Federation (Entra token exchanged at Google STS, attribute condition on the identity's object id, impersonation of a narrow service account or direct principal binding), no keys; read tools scoped to the engagement, write tools behind approval tokens; per-tool identities for GitHub/ServiceDesk/GRC. Partial: managed identity only. Zero: service account key in Key Vault. |
| 4 | Data, residency and retention | 15 | Full: Blob with private endpoints, version-level immutability / time-based retention (WORM) 7 years for evidence, workpapers and logs, legal hold; US regions on both sides; enterprise terms (no training on data), prompt/response logging owned by MFH; PII minimization before the model. Partial: missing immutability or residency on one side. |
| 5 | Traceability | 10 | Full: per step and per call log (inputs, tool calls, model id and version, prompt/config hash, response, citations, reviewer decision), hash-chained or immutable, linked from each workpaper conclusion; re-performance walkthrough. |
| 6 | Evals and change management | 15 | Full: ControlPilot under CM-03 itself: prompts, model version, tool permissions and code versioned in git, ticketed, independently approved, eval gate in CI per control (exception recall), pinned model versions, quarterly metrics to the committee, regression rerun on model deprecation. Partial: evals without the change-control loop. |
| 7 | Threat model | 10 | Prompt injection through evidence files, lethal trifecta broken (no exfiltration channel from the evidence-reading agent, no write tools there), egress allow list, tool-argument validation, model outage fallback, residual risk stated. |
| 8 | Cost model and rollout | 10 | Cost computed from 600 items x ~40k in / 3k out (plus caching assumptions and Azure costs), peak of 150 items in 10 days; phased rollout (one control, parallel run against humans, exit criteria). |
| 9 | Clarity | 10 | A diagram, decisions with reasons, readable by a non-engineer committee advisor; ANSWER.md summarizes the five key decisions and rejected alternatives. |
Total: 100
