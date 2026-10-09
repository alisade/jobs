# ms/w9-c1 answer (model)

## Approach
ResetPassword branches on an explicit "own account?" Boolean question before anything touches the reset
flow, so the dangerous path is the else branch, not an afterthought. The flow status drives a second
ConditionGroup whose else branch is the failure path (any status other than Success escalates, which
fails safe if the flow ever returns a new status). Escalation context travels in one Global variable,
`Global.EscalationReason`, set by whoever starts the escalation and defaulted to `UserRequested` in
Escalate itself, which also clears it afterwards. Fallback uses the platform `System.FallbackCount`
instead of a home-made counter, because the platform already resets it when a topic is recognized.

## Fix
- Added an ownership gate, a system question, the reset flow call and success/failure branches.
- modelDescription now states what the topic does, when to use it and what it does not handle; that
  text is what generative orchestration matches against, trigger phrases are only examples.
- Fallback escalates on the third consecutive miss with reason `Unrecognized`.
- Escalate passes `upn`, `reason`, `summary` and resets the reason.
- Verified with the simulator scenarios; would repeat them in the test pane with the activity map.

## Trade-offs / what I would do in production
- Require authentication (Entra ID) so `System.User.PrincipalName` is trustworthy; the reset flow must
  re-check identity server-side, never trust the topic.
- Make the reset a tool (agent flow) with a good description too, so orchestration can call it directly,
  but keep the ownership check inside the flow.
- Log escalation reasons as custom telemetry (Application Insights) and track containment/escalation rate.
- Build an evaluation test set (wrong-account, MFA, rephrase loops) and run it on every solution import.
