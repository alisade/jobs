# Design: ControlPilot production architecture and control-owner review pack

## Context and requirements

ControlPilot performs testing steps for six ITGCs (about 600 sample items a year, peak 150 items in
10 business days). It never signs off. Committee conditions (C1-C7) and standards (SEC-02..SEC-11)
are mapped to mechanisms in the table at the end of each section. Out of scope for FY2026: SAP
controls, autonomous remediation, anything outside internal audit's engagement data.

## Architecture overview

```text
 Reviewers (IT audit seniors)            Entra ID (SSO, groups: cp-preparers, cp-reviewers, cp-admins)
        |                                        |
        v                                        v
 [Review UI: Container App] ---> [Orchestrator: Azure Durable Functions (Flex Consumption, VNet)]
                                    |   per run: sampling -> per item sub-orchestration
                                    |   activities: fetch evidence, extract, evaluate, publish
                                    v
            +-----------------------+---------------------------+--------------------------+
            |                       |                           |                          |
   [Tool gateway: Container App]  [Blob: evidence, workpapers,  [Azure SQL: run state,      [Event Hub -> Sentinel
    read tools per engagement      execution log; private EP,    review queue, idempotency   and Log Analytics]
    write tools need approval      version-level WORM 7 yrs]     keys]
            |
   GitHub (GitHub App, read) / ServiceDesk (read) / GRC Hub (write behind approval)

   Agent calls: Orchestrator activity -> egress firewall (FQDN allow list) -> Google STS (WIF)
                -> Gemini on Gemini Enterprise Agent Platform, us-central1, pinned model version
```

Durable Functions (not Agent Runtime) hosts the orchestration because state, retention and the
review gate must live in MFH's Azure estate under its logging and immutability controls; Google
hosts only the model. The agent loop is ADK running inside activities with a custom tool layer, so
the same code runs in tests with a scripted model.

## Execution model: orchestration, state and review checkpoints

- A run = one control x one test period. The orchestrator draws the sample deterministically (seed
  recorded), then starts one sub-orchestration per item; fan-out limited to 10 concurrent items.
- Each activity is idempotent: side effects carry an idempotency key `run_id/item_id/step`; blob
  writes use If-None-Match; GRC issue creation looks up the key before creating. Checkpoints are
  Durable's event history plus a row per step in Azure SQL.
- Review gate: every exception, every not_evaluable item and a random 10% of passes raise an
  external event wait (`WaitForExternalEvent("review")`) with no timeout; runs pause for days.
  The reviewer decision (approve / override with reason and evidence reference) is accepted only if
  the reviewer's Entra object id differs from the preparer of record and is in cp-reviewers.
- Kill switch (C7): an App Configuration flag checked before every activity plus the cp-admins
  runbook that disables the Function app's role assignment on the tool gateway; measured in drills
  at under 5 minutes. Running orchestrations suspend, they are not lost.

## Identity, access and tool scoping

- Each component has a user-assigned managed identity (SEC-02). No secrets in settings.
- Azure to Google: the orchestrator's managed identity gets an Entra token for an app ID URI, and
  Google STS exchanges it through a Workload Identity Pool provider (issuer = the Entra tenant,
  attribute condition on `assertion.sub` = the identity's object id). The federated principal is
  granted `aiplatform.user` on the project directly or impersonates one narrow service account.
  No service account keys exist; an org policy blocks key creation.
- Tool gateway: read tools scoped by engagement id (only sampled items, only the period); write
  tools (create GRC issue, attach workpaper) require an approval token minted by the review gate.
  GitHub access is a GitHub App with read-only contents/pull-request scope on in-scope repos.
- The agent that reads evidence has no write tools at all (see threat model).

## Data flow, residency and retention

- Evidence is copied into a per-engagement Blob container (private endpoint) with a content hash.
  Workpapers and the execution log go to separate containers. Version-level immutability with a
  7-year time-based retention policy, locked after sign-off; legal hold available (C3, SEC-07).
- Google side: us-central1 only, enterprise terms (no training on customer data), request/response
  logging done by MFH in its own log (SEC-09); no data stored by the agent platform beyond the call.
- PII: employee names stay as directory ids where possible; evidence text is minimized to the
  pages retrieved.

## Traceability: evidence citations and the execution log

Per step: run id, item id, step, inputs hash, tool calls with arguments and results, model id and
version, prompt and config hash, response, usage, citations (blob path, version id, page or cell),
reviewer decision. Records are hash-chained and written to the immutable log container and to
Sentinel. Every workpaper conclusion links to its citations and to its log entries, so the external
auditor re-performs an item by opening the cited evidence versions and the rule that consumed them.

## Evaluation, monitoring and change management

- ControlPilot is under CM-03 (C5): prompts, model version, tool permissions and code live in git;
  every change needs a ServiceDesk ticket, an approver other than the author and a passing CI eval
  gate (per-control labeled sets, exception recall >= 0.95, accuracy within 2 points of baseline).
  A model version is pinned; a provider deprecation triggers the same release path.
- Quarterly committee pack (C4): accuracy, exception recall, consistency, cost, override count per
  control from the eval harness and the review queue.
- Monitoring: orchestration failures, review queue age, model error rate and latency, cost per item,
  alerts to the on-call engineer; security events to Sentinel within 5 minutes.

## Threat model

| Threat | Mitigation | Residual |
|---|---|---|
| Prompt injection in an evidence file | evidence is data in user content; the reading agent has no write tools; conclusions need citations validated in code | a manipulated extraction reaches a reviewer, who sees the citation |
| Lethal trifecta | no exfiltration channel: egress allow list to Google only, no web or e-mail tools | low |
| Privilege escalation through tools | gateway validates arguments against the engagement scope; writes need approval tokens | low |
| Credential theft | no keys; WIF tokens are short-lived and condition-bound | low |
| Model outage or drift | retries with backoff, items park in a queue; pinned version, eval gate | delays at peak |

## Cost model

600 items x 40k input + 3k output tokens = 24M input and 1.8M output tokens a year. At illustrative
prices of $0.30 and $2.50 per 1M tokens that is about $12 a year for production calls; quarterly
evals (6 controls x 30 samples x 5 runs x 4) add about $70. Azure (Functions, Container Apps, SQL,
storage, Sentinel ingestion) dominates at an estimated $600-900 a month. The real cost is reviewer
time, so the cost lever that matters is fewer false exceptions, not cheaper tokens.

## Risks, open questions and rollout plan

1. Pilot CM-03 in the Q4 interim period in parallel with manual testing; exit criteria: exception
   recall 1.0 on the parallel sample, zero unexplained differences, reviewers' time per item down.
2. Add CM-05 and AC-04, then the user access review.
Decisions needed: the committee accepts 10% pass re-review; the external auditor agrees to rely on
the execution log format; Google region confirmation under the enterprise agreement.
