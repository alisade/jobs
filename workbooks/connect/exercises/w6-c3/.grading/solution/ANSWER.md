# ANSWER: connect/w6-c3 QA and compliance monitoring program

## Approach

Started from the risks and the capacity numbers in the inputs, then chose the trigger for each risk
(real-time where a supervisor can still act, post-contact otherwise) and moved human time to risk-based
samples.

## Fix

- 100% automated coverage with conversational analytics rules; real-time for credential requests, card
  digits and escalations; post-contact categories and automated evaluations for adherence.
- Generative AI evaluations for judgement questions, validated in shadow against humans first.
- Human reviews re-allocated to auto-fails, low scores, new hires and a random floor (~1,080/month).
- Monthly cross-site calibration; vendor bonus on calibrated or automated scores.
- Coaching as ServiceNow tasks with a 5-day SLA; redacted data only, TBAC by site.

## Trade-offs / what I would do in production

Automation gives coverage but must earn trust: shadow periods and human review of auto-fails cost time
up front. Removing vendor self-scoring from the bonus needs a contract change. First pilot validation:
false-positive rate of the credential-request rule on one team.
