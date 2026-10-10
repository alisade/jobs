# Design: LFG service desk QA and compliance monitoring program

## 1. Goals, scope and success measures

Goal: every contact checked automatically for the risks that can hurt LFG; human QA time spent where it
changes behavior; one defensible score across LFG and both vendors. In scope: voice and chat now, email
from Q1 2027; agents and team leads at all three sites. Out of scope: WFM adherence, IVR/bot quality.

| Measure | Baseline | Target (6 months) |
|---|---|---|
| Contacts checked for compliance risks | 2% voice, 0% chat | 100% voice and chat |
| Credential-request incidents reaching a supervisor during the call | 0% | 90% |
| LFG vs vendor score gap on calibrated contacts | 9 points | <= 3 points |
| Dispute rate / dispute cycle time | 15% / 2 weeks | < 7% / 5 business days |
| Coaching task created and closed within 5 business days | not tracked | 90% |
| Disclosure compliance on password/MFA contacts | unknown | 98% |

## 2. Operating model

| Activity | LFG QA (3) | Team leads | Vendor QA (Pune, Monterrey) | Compliance | Platform team |
|---|---|---|---|---|---|
| Rules and categories (content) | A | C | C | R (risk rules) | R (deploy as code) |
| Evaluation form | A/R | C | C | C | I |
| Human evaluations | R (LFG agents, risk samples) | I | R (own agents) | I | - |
| Calibration | A/R (facilitate) | C | R | I | - |
| Coaching | I | A/R | R (vendor leads) | I | - |
| Disputes | A | R | R | C | - |
| Access, retention, PCI | C | - | - | A | R |

Agents are told how monitoring works in onboarding and in a one-page notice agreed with the Monterrey
works council and referenced in the Pune vendor contract.

## 3. Detection layer: categories and rules

| Rule | Trigger | Condition sketch | Action | Owner |
|---|---|---|---|---|
| Credential request (voice) | OnRealTimeCallAnalysisAvailable | AGENT says "your password", "MFA code", "read me" | notification to team lead + EventBridge event -> ServiceNow security task | Compliance |
| Credential request (chat) | OnRealTimeChatAnalysisAvailable | same phrases, AGENT | same | Compliance |
| Card digits | OnRealTimeCallAnalysisAvailable | CUSTOMER says "card number", digit pattern match | notification to team lead | Compliance |
| Escalation language | OnRealTimeCallAnalysisAvailable | CUSTOMER "supervisor", "complaint" + negative sentiment | notification to floor supervisor | QA |
| Disclosure missing | OnPostCallAnalysisAvailable | category PasswordMFA AND NOT agent disclosure phrase | category + SUBMIT_AUTO_EVALUATION | QA |
| SOX access approval | OnPostCallAnalysisAvailable | category AccessRequest AND NOT "manager approval" | category + task for team lead | Compliance |
| Call drivers | OnPostCallAnalysisAvailable / OnPostChatAnalysisAvailable | keyword groups | category only | QA |

Rules live in git as AWS::Connect::Rule and are promoted dev -> test -> prod with the flows.

## 4. Evaluation forms and automated evaluation

Form "Service Desk Contact Quality v1": Compliance (auto-fail: credential request, card data handled,
SOX approval skipped), Resolution (correct fix, ticket updated, first-contact resolution), Customer
experience (greeting, empathy, closing), Documentation. Compliance items answered by rules; greeting and
closing by rules; empathy, resolution and documentation by generative AI performance evaluations
(natural-language criteria, answer plus justification with transcript references). For 6 weeks
automated answers run in shadow: humans score the same 300 contacts, agreement per question must reach
85% before the automated answer counts; auto-fails always get a human review before they affect pay.

## 5. Sampling strategy

Automated coverage: 100% of voice and chat. Human capacity: 3 analysts x ~120 productive hours = 360 h,
at 20 minutes per review (pre-filled automated answers) = ~1,080 reviews/month. Allocation: all
auto-fails (~150), lowest 5% automated scores (~400), new hires in first 60 days (4 per agent per month,
~120), random floor of 2 per agent per month (280), calibration set (30). Vendors review their own agents
on the same rules with LFG auditing 10% of vendor reviews.

## 6. Calibration and disputes

Monthly 90-minute calibration: 10 contacts scored blind by LFG QA, both vendor QA leads and two team
leads; agreement = share of questions within the same answer, target 85%, and score spread <= 5 points.
Vendor bonus uses automated scores plus LFG-audited human scores, removing self-scoring bias. Disputes in
ServiceNow, team lead first (2 days), LFG QA final (5 business days).

## 7. Coaching loop

Finding or low score -> ServiceNow coaching task to the team lead (vendor lead for vendor agents) with the
contact link and the rule or question; due in 5 business days; closure needs a note and a follow-up check
(next 5 contacts of that agent automatically reviewed for the same item). Three repeat findings in 30 days
escalate to the site manager; credential requests escalate to Compliance immediately.

## 8. Data, privacy and access

QA uses redacted analysis and redacted audio only; originals (RedactedAndOriginal for legal hold) are
readable only by the legal role. Tag-based access control on security profiles so vendor leads see only
their site's agents, queues and evaluations. Real-time voice analytics is not redacted (redaction runs
after disconnect), so alerts carry contact links, never transcript text. Retention: evaluations 2 years,
redacted analysis 13 months, originals per legal hold. Help desk is out of PCI scope by policy: card
digits trigger a stop-the-caller alert and a security task.

## 9. Reporting

Monthly service review: coverage, compliance rule hits per 1,000 contacts by site, disclosure rate,
calibrated quality score by site and team, dispute rate and cycle time, coaching SLA, top call drivers.
Sources: rule events and categories, evaluations, the Connect analytics data lake queried with Athena.

## 10. Rollout plan and risks

Phase 1 (4 weeks): rules in shadow on one Charlotte team; tune phrases on false positives. Phase 2: all
voice, form v1 human-only, calibration starts. Phase 3: generative AI evaluations in shadow, then live
per question. Phase 4: chat, Spanish pilot. Q1 2027: email.
Risks: false positives erode trust (shadow period, phrase tuning, human review of auto-fails); works council
objection (early notice, no automated pay decisions); vendor pushback on bonus change (contract amendment,
3-month transition); cost (bundled AI pricing on Connect Customer, monitor usage).

## Diagram

```text
contact (voice/chat) -> conversational analytics (real-time + post-contact, redacted)
   |-- real-time rules --> supervisor notification / EventBridge -> ServiceNow security task
   |-- post-contact rules --> categories + automated evaluation
   v
evaluation (automated + generative AI + human sample) -> calibration (monthly)
   v
coaching task (ServiceNow, 5 days) -> follow-up auto review -> escalation
   v
reporting (data lake + Athena) -> monthly service review
```
