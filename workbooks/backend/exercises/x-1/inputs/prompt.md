# Prompt (read aloud by the interviewer)

"Lumenfold's apps run on a CRM today, and about 140 flows and triggers in it automate things: assign a
lead, ask a manager to approve a discount, create a renewal 120 days before a contract ends, notify the
deal desk when a big opportunity moves stage. We are replacing the CRM with Keystone. Design the
workflow automation service that product teams self-serve on Keystone, so they can build those
automations without filing tickets with the platform team. Assume we have decided on Temporal as the
engine. Go."

## Facts you may ask for (the interviewer gives these if asked)

- Four product teams today, maybe ten in two years. Six tenants (business units and apps).
- Volumes: about 9,000 opportunity stage changes per business day, 1.1 M activities a month, a few
  thousand approvals a week. Renewal creation runs for about 180,000 contracts.
- Most automations are event-triggered (a stage changed, a lead was created); some are scheduled.
- Approvals can wait days; escalation after 48 hours is the norm.
- Agents (a sales assistant) will want to start some of these automations.
- The platform team is five engineers. They operate the Temporal cluster.
