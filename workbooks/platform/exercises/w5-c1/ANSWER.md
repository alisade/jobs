# ANSWER: platform/w5-c1 Admission gate for Helm-rendered manifests

## Approach

<!-- How you structured the rules; which cases you tested first; anything in the spike you did not trust and why. -->

## Fix

<!-- What the gate reports on the shipped render, and what each chart owner (riq-api, rdm-worker) must change. -->

## Trade-offs / what I would do in production

<!-- CI gate vs Binary Authorization at admission (and Policy Controller or Gatekeeper if you would add one);
dry-run rollout and how long; who approves break-glass and how it is audited (Cloud Audit Logs, alert);
attestation by the build pipeline (SLSA provenance, Artifact Analysis vulnerability gate); what the gate
cannot see (runtime, images pulled by operators, Helm hooks). -->
