# Requirements for the CRM/ITSM integration (from the design workshop, 2026-10-02)

R1  Screen pop on answer: caller identity, verification status, bot summary/intent, open incidents or cases.
R2  One contact -> exactly one ticket reference (incident or HR case), never duplicates on retries.
R3  Agents use the system they already live in: IT agents in the Connect agent workspace with ServiceNow
    alongside; People Desk agents inside Salesforce Lightning.
R4  Contact record (ContactId, channel, queue, agent, timestamps, recording link, Contact Lens summary)
    logged on the ticket.
R5  Click-to-dial from the ticket for callbacks (IT: ServiceNow; HR: Salesforce).
R6  LFG keeps ownership of telephony, flows, data and the AWS bill (Finance and Security requirement):
    contact data must stay in LFG's AWS account.
R7  One Connect instance for both business units if possible (shared numbers, shared IVR front door,
    shared WFM), with separate routing, security profiles and reporting.
R8  SSO for agents via Okta, no separate Connect passwords.
R9  PII: no SSN or payroll data in contact attributes; HR case details stay in Salesforce.
R10 Run by a team of 2 onshore + 4 offshore engineers after hypercare.
