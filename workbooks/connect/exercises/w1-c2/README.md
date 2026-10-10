# connect/w1-c2 - Help desk instance as code (CDK)

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 1 (Mon: instance model; Wed: queues and routing profiles; Thu: IaC for Connect)

## Scenario

LFG's platform team stands up one Amazon Connect instance per environment (dev in
111122223333, prod in 444455556666) from the same CDK app. The pilot stack was written by
hand against dev: it has no routing profiles, UTC hours, every queue on the staffed hours
(so outage reports bounce at 8 PM), and the contractor string-replaced dev ARNs into the
inbound flow, so the prod pipeline would deploy a flow that points at dev queues and
Lambdas. The change advisory board will not approve prod until the stack is config-driven
and environment-safe.

Everything is driven by `config/helpdesk.json` (hours, holidays, queues, routing profiles,
Lambda names, Lex intents) and `flows/helpdesk-inbound.template.json` (the flow from
w1-c1 with `${QueueGeneralSupport}`-style placeholders). Synth runs offline with
`aws-cdk-lib` L1 constructs (`aws-connect`, `aws-lex`): CloudFormation has resource types
for these, so no custom resources are needed here.

## Requirements

1. Instance: SAML identity, inbound/outbound calls, flow logs, Contact Lens (conversational
   analytics), early media. Retained on stack deletion in prod only. Tagged with the
   config tags plus `Environment`.
2. Hours: every entry in `config.hours`, in `config.timeZone`. Each holiday in
   `config.holidays` becomes a `CLOSED` hours override (one day, `EffectiveFrom ==
   EffectiveTill`) on `HelpDeskHours` only; the 24x7 `Always` hours have no closures.
3. Queues: one per `config.queues`, each on its own configured hours.
4. Routing profiles: one per `config.routingProfiles`, voice and chat media concurrency
   from config (route current channel only), every queue entry configured for both VOICE
   and CHAT with its priority and delay, default outbound queue `GeneralSupport`.
   A routing profile that names an unknown queue fails synth with a message naming it.
5. Integrations: associate both Lambdas (by name, ARN built for the deploying account and
   region) and the Lex bot alias with the instance.
6. Lex V2 bot `lfg-helpdesk-bot-<env>`: `en_US` locale at the configured confidence
   threshold, the configured intents with their utterances, plus `FallbackIntent`; a
   numbered bot version and a `live` alias on that version (Connect must not point at
   `TestBotAlias`/DRAFT).
7. Flow: one `ACTIVE` `CONTACT_FLOW` whose content is the template with every placeholder
   resolved by `Fn::Sub` to this stack's resources (queues and hours via `GetAtt`).
   No account-specific ARN in the flow body. A placeholder without a matching resource,
   or malformed template JSON, fails synth.
8. An unknown environment name fails fast.

## Acceptance criteria (what the grader checks)

- Template assertions (`aws-cdk-lib/assertions`) for every requirement above, for both dev and prod.
- Config changes (a new holiday, a typo in a routing profile) behave as specified without code changes.
- `ANSWER.md`: why `Fn::Sub` tokens instead of string replacement, what CloudFormation cannot
  manage for Connect today and how you would handle it, and how flows get promoted between environments.

## How to run

```bash
make setup               # link the shared toolchain (connect/_env)
make synth ENV=prod      # print a synthesized template
make test                # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w1-c2
make clean
```
