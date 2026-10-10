# Reference: connect/w7-c4

Model answer: `.grading/solution/DESIGN.md`.

What great looks like:

- Starts from the constraints that eliminate options: LFG must own the instance and the data (R6) on one
  instance (R7). The Service Cloud Voice bundle provisions the Connect instance in a Salesforce-managed AWS
  account and bills through Salesforce, so it fails both. The CTI Adapter (AppExchange package + serverless
  app in LFG's account) and SCV partner telephony ("bring your own Amazon Connect") both keep LFG's instance.
- Honest about ServiceNow: AWS documents Customer Profiles AppFlow mappings for ServiceNow (profiles and
  standard case objects) and a ServiceNow knowledge connector for agent assist; the in-ServiceNow softphone
  ("ServiceNow Voice with Amazon Connect") is ServiceNow's product. A custom integration on the Table API
  with an agent workspace app is a legitimate, common choice for IT help desks.
- Separates the agent desktop decision from the ticket-writing path; makes logging event-driven and
  idempotent (ContactId as the key, conditional writes, external id / correlation_id).
- Uses one instance with tag-based access control and separate routing/reporting per line of business.
- Names the operational coupling (managed package releases, ServiceNow family upgrades) and sizes it
  against the post-hypercare team.

Common misses: claiming an AWS-built ServiceNow CTI adapter; treating SCV as one thing; relying on agents
to log the call; forgetting transfers/persistent chat when choosing the idempotency key.
