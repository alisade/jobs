# ANSWER: connect/w1-c2 Help desk instance as code (CDK)

## Approach

Made every resource a loop over config/helpdesk.json and checked templates for both envs with make synth.

## Fix

Instance attributes and retain-in-prod; per-hours time zone and CLOSED holiday overrides on staffed hours;
queues on their own hours; routing profiles with voice/chat concurrency and per-channel queue configs;
Lambda and Lex alias integration associations; bot + version + live alias; flow content via Fn::Sub with a
synth-time check that every placeholder has a resource. Verified with make test.

## Trade-offs / what I would do in production

Split long-lived (instance, numbers) and fast-changing (flows, queues) stacks; users via SAML from the IdP;
detect console drift on flows; flows have no alias in CFN, so promote by template + Fn::Sub per env.
