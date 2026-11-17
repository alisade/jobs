# ANSWER: platform/w6-c1 plan-gate: a Terraform plan JSON gate for CI

## Approach

Classification and validation first (fail closed on anything unknown), then summary, diff with
masking, policy and the CLI. Tested with the fixtures plus inline plans for edge cases.

## Fix

Implemented Classify/Validate/Summarize, ChangedAttributes with depth-aware masking, Evaluate with
the three rules, and Run/Build with exit codes 0/1/2 and a stable JSON report.

## Trade-offs / what I would do in production

- The plan JSON is what will be applied: provider defaults and ForceNew attributes only show there.
- Gate the saved plan file that the apply job consumes, not a re-plan.
- Cannot see unknown-after values, provider bugs or drift outside the state; complements
  gcloud beta terraform vet / OPA rather than replacing them.
- Ship as a pinned binary in a shared CI template; policies per repo class; audited break-glass label.
