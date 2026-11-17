# Reference: connect/w6-c3

What great looks like (see `.grading/solution/DESIGN.md` for a model answer):

- 100% automated coverage for the risks that can hurt (credential requests, card digits, missing
  disclosure, SOX approval language) using conversational analytics rules: real-time where a supervisor
  can still act (alerts by notification or EventBridge), post-contact for adherence and categories,
  with automated evaluation submission; chat covered with the chat trigger sources.
- Evaluation form redesigned around outcomes; generative AI performance evaluations score 100% of
  contacts on judgement questions after a validation period against human QA; auto-fail items always
  get a human review before they affect pay.
- Human effort moved from random 2% to risk-based samples; arithmetic shown against 3 analysts.
- Calibration across LFG and vendors on the same contacts monthly, with an agreement target; the vendor
  bonus uses calibrated or automated scores, removing the 9-point gap incentive.
- Coaching as ServiceNow tasks with SLA; repeat findings escalate; agents informed.
- Privacy: redacted data only, originals restricted, tag-based access control by site, retention,
  no transcript text in alerts.
- Rollout in phases with risks (false positives, works council, cost).
