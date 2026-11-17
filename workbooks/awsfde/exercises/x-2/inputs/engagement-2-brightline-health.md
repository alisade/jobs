# Engagement note 2: Brightline Health (2026-10-02), tool read tenant from its arguments

FDE on site: one engineer, three days, during the customer's pen test.

- Symptom: the pen tester asked the agent "show ticket TK-0000A001 for tenant acme-foods" and the
  ticket-lookup tool returned Acme's ticket.
- Cause: the tool Lambda behind AgentCore Gateway used `args.get("tenant_id") or claims["tenant_id"]`
  because "the agent needs it for admin users". The Lambda role could read the whole table.
- One-off fix: tenant from the verified JWT claim only; a separate admin tool with its own Gateway
  target and authorizer; the role restricted with dynamodb:LeadingKeys on a tenant_id session tag
  (ForAllValues:StringLike, no Scan). Hand-written IAM in that one repo.
- Left behind: the policy JSON in a CDK stack in Python, three attack tests in pytest.
- Two other tool Lambdas in other teams' repos were found with the same pattern and fixed by hand.
