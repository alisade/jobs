# ANSWER: connect/w7-c4 CRM/ITSM integration design

## Approach

Started from the hard constraints (R6 ownership, R7 single instance), which eliminated the Service Cloud
Voice bundle, then scored the remaining options against R1-R10 and separated "where the agent works"
from "how tickets get written".

## Fix

- One LFG-owned Connect instance; IT on the agent workspace + help desk app, HR on the CTI Adapter in Salesforce.
- Context travels as contact attributes, readable by both desktops.
- Event-driven, idempotent contact-to-ticket logging keyed on ContactId with a DynamoDB ledger.
- TBAC security profiles split the two lines of business on one instance.
- Service Cloud Voice partner telephony kept as the 2027 option for HR.

## Trade-offs / what I would do in production

More custom code to own on the ServiceNow side in exchange for control and one instance; a two-week POC
of the CTI Adapter in a Salesforce sandbox and of the EventBridge logging path before committing.
