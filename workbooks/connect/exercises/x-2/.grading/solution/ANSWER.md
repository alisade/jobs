# ANSWER: connect/x-2 The assistant refuses password resets after the security fix

## Approach

Filtered the invocation logs for guardrail interventions, read the traces and token usage, then
compared the trace topic with guardrail/helpdesk-guardrail.json and replayed evals with make evals.

## Root cause

`jq` over incident/invocation-logs shows reset requests with `"stopReason":"guardrail_intervened"`,
`"usage":{"inputTokens":0,...}` and `inputAssessment ... "topicPolicy":{"topics":[{"name":"Credentials and
account access","type":"DENY","action":"BLOCKED"}]}`. The topic (version 3) is defined as "Any request about
passwords, credentials, logins, MFA, account unlocks or account access" with sample phrases "my password",
"unlock my account", "reset password": it denies the exact self-service the assistant exists for. Blocked
before the model, so the prompt line is not involved (0 input tokens). make evals: 19/28 (9 legit blocked).
{USERNAME} is the USERNAME PII ANONYMIZE output action, working as configured. Metrics: resets completed by
the assistant 522 -> 61 on 2026-10-01 with handoff_reason_guardrail 3 -> 688.

## Fix

Replaced the topic with "Other peoples passwords" and "Account takeover" (third-party, privileged/service
accounts, verification bypass) with specific sample phrases; kept PROMPT_ATTACK HIGH and PASSWORD BLOCK.
make evals 28/28 and the held-out style variants pass. Published as version 4, GUARDRAIL_VERSION=4.

## Trade-offs / what I would do in production

Eval gate with ApplyGuardrail against the real classifier before publishing versions; held-out red-team set
owned by security; canary the version; alarm on guardrail handoff rate.
