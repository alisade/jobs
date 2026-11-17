# Constraints for the reusable kit

- About 14 service teams. Half write Lambdas and CDK in TypeScript, half in Python. Agent tools sit
  behind AgentCore Gateway (Lambda targets); the agent runs on AgentCore Runtime. AgentCore CDK L2
  constructs are stable in aws-cdk-lib/aws-bedrockagentcore (only Policy is still alpha).
- Two-week release cadence. Teams will not adopt anything that adds more than a day of work per service
  or a new runtime dependency they do not control.
- Security review (Tidewater's AppSec team) must sign off any change on a tenant-data path; today that is
  a manual checklist and takes up to a week.
- Shared platform team: three engineers. They can own a small library and a CDK construct package, not
  a platform service.
- Customers (Brightline in particular) ask for evidence of tenant isolation in their vendor reviews.
- Budget: no new paid tools this quarter.
