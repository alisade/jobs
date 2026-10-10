# connect/w6-t2 - Real-time supervisor alert never fires

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 6 (real-time vs post-contact analytics, conversational analytics rules and alerts); Week 1 (flow modules)

## Symptom

CHG0034502 (2026-09-30) promised Larkspur's floor supervisors an alert email while an upset caller is
still on the line ("speak to your supervisor"). Three callers escalated this week and nobody was
alerted until the next morning, when the post-call category showed up in the QA dashboard. The rule
is published, the phrases are the same as the weekly post-call rule (which works), and the change was
tested successfully in the sandbox flow. Supervisors say they "see the live transcript for a few
seconds in the IVR, then it stops". Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` | page and thread, both rules (DescribeRule output), flow logs for the three calls, post-call analysis excerpts, the EventBridge archive of rule matches, Kinesis consumer metrics, the change record (created by `make setup`) |
| `flows/helpdesk-inbound.json` | the inbound flow (v14, flow language) |
| `flows/modules/mod-recording-defaults.json` | flow module invoked before every queue transfer (PCI redaction defaults, used by several flows) |
| `rules/escalation-language-live.json` | the real-time rule as deployed by the pipeline (AWS::Connect::Rule input) |
| `config/` | resource ARNs and the module id |

## Your task

1. Find the root cause with evidence from the flow logs and the flow/module JSON, and explain why
   the sandbox test passed. Rule out the red herring with a reason.
2. Fix it so real-time analytics is in effect when the agent is talking to the caller on every
   path that reaches a queue, without losing the PCI redaction defaults the module applies (the
   module must still run before every transfer).
3. Do not "fix" it by turning the alert into a post-call rule: supervisors need it while the caller
   is on the line.
4. `make lint`, `make test`.
5. `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix and verification,
   prevention.

## Acceptance criteria (what the grader checks)

- On the GeneralSupport, PasswordReset, VIP and after-hours outage paths the effective (last applied)
  analytics settings at transfer include RealTime, with redaction still enabled and RedactedOnly.
- The module still runs before every transfer; every analytics block records both participants in
  en-US and wires NoMatchingError and ChannelMismatch; no block in the path selects PostContact.
- The rule remains a published real-time rule on both queues with the customer phrase condition.
- `ANSWER.md` names the mechanism with evidence.

## How to run

```bash
make setup     # incident bundle + shared toolchain
make lint      # graph checks for the flow and the module
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w6-t2
make clean
```
