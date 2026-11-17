# audit/x-2 - ControlPilot production architecture and control-owner review pack

**Type:** design | **Estimate:** 2-3 hours | **Study plan:** Week 7 add-on (Mon: Workload Identity Federation; Tue: Azure hosting and immutable storage; Wed: Gemini Enterprise Agent Platform; Fri: architecture review prep)

## Scenario

ControlPilot works on the bench: it extracts evidence with Gemini, cites it, pauses for review and
passes its evals. Before the FY2026 year-end cycle, the MFH audit committee, the CISO's architecture
review and the external auditor's IT specialist want one document that shows how it runs in
production. Their conditions are in `inputs/`: human sign-off, evidence citations, 7-year immutable
retention, quarterly metrics, a kill switch, no long-lived credentials, US-only data, and the
uncomfortable one: ControlPilot is itself an in-scope application, so its own code, prompts, model
version and tool permissions are subject to the CM-03 program-change control it tests.

Azure is the MFH standard platform; Google Cloud is approved only for the Gemini models, reached
through Gemini Enterprise Agent Platform (the current name for what older material calls Vertex AI).

## What you have

| Path | What it is |
|---|---|
| `inputs/audit-committee-requirements.md` | the committee's seven conditions |
| `inputs/it-security-standards.md` | the security standards that apply |
| `inputs/volumes-and-constraints.md` | controls, volumes, systems, team, peak |
| `DESIGN.md` | the template you fill in |
| `ANSWER.md` | your summary of decisions and trade-offs |

## Your task

1. Fill in every section of `DESIGN.md`: architecture with a diagram, execution model with review
   checkpoints, identity and tool scoping (Workload Identity Federation from Azure to Google, no
   keys), data flow, residency and retention (immutable storage for evidence and workpapers),
   traceability, evals and change management (including ControlPilot under CM-03), threat model,
   cost model from the volumes, and a rollout plan.
2. In `ANSWER.md`, give the five decisions you would defend first and the alternatives you rejected.

## Acceptance criteria (what the grader looks for)

- Every committee condition and security standard is answered by a named mechanism, not a promise.
- Write tools sit behind approval; read tools are scoped to the engagement; no keys anywhere.
- Retries cannot duplicate side effects; runs can pause for days at a review gate and resume.
- An external auditor could re-perform a sample item from the workpaper and the execution log.
- A prompt or model change is a ticketed, independently approved, eval-gated release.
- The cost estimate is computed from the volumes, with the assumptions stated.

## How to run

```bash
make setup     # nothing to install; read inputs/
make test      # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code: /grade audit/x-2
make clean
```
