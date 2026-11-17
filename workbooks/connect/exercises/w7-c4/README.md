# connect/w7-c4 - CRM/ITSM integration design: ServiceNow vs Salesforce

**Type:** design | **Estimate:** 2 hours | **Study plan:** Week 7 (ServiceNow and Salesforce integration, screen pops, Cases, Customer Profiles); Week 2 (solution design deliverables)

## Scenario

Larkspur Financial Group runs IT support in ServiceNow ITSM and HR shared services ("People Desk") in
Salesforce Service Cloud. Both move from Avaya onto one LFG-owned Amazon Connect instance: IT in wave 1,
People Desk in wave 3. The architecture review board wants one document that decides, for each line of
business, where agents work, how the screen pop and click-to-dial work, how every contact ends up on a
ticket, and who owns what afterwards. Salesforce's account team is pushing the Service Cloud Voice bundle;
the ServiceNow team asked about ServiceNow's own Connect integration.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-state.md` | systems, volumes, pain points, audit ask |
| `inputs/requirements.md` | R1-R10 from the design workshop |
| `DESIGN.md` | the template you fill in (the deliverable) |
| `ANSWER.md` | short summary of your approach and decisions |

## Your task

1. Fill in `DESIGN.md` for the review board (1,500-2,500 words, a diagram, one IT and one HR call walked
   end to end, a decision record).
2. Be precise about ownership and billing of the Connect instance in each Salesforce option (Amazon Connect
   CTI Adapter, Service Cloud Voice bundle, Service Cloud Voice with partner telephony from Amazon
   Connect), and about which ServiceNow capabilities AWS documents versus what ServiceNow provides.
3. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

There are no automated tests: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0,
"total": 0}`. The rubric carries all 100 points: option accuracy, requirements traceability, the ticket
logging design (idempotency, event source, traceability), security and multi-LOB access control,
operability and risk, and communication.

## How to run

```bash
make test      # completeness report: which sections are still empty
# then from workbooks/ in Claude Code: /grade connect/w7-c4
```
