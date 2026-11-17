# Design: LFG help desk multi-region resiliency and DR runbook (model answer)

## Context and requirements

- Voice RTO 15 min, chat RTO 30 min, RPO 15 min for contact records and recordings; drills twice a
  year with <= 5 min employee-visible impact. Primary us-east-1, secondary us-west-2.
- In scope: Connect instance, numbers, flows, queues/routing, agents, Lambdas, Lex, DynamoDB, S3/KMS
  for recordings and transcripts, analytics export. Out of scope: Okta and ServiceNow internal DR
  (vendor responsibility) except our network/allow-list dependencies on them; Avaya trading floor.
- Security architecture requires an AWS-supported pattern: Amazon Connect Global Resiliency (ACGR) is
  the AWS-supported multi-region option for Connect; a DIY second instance with re-pointed numbers is not.

## Target architecture

```text
                       Okta (SAML IdP, global sign-in endpoint for Connect)
                                          |
   employees --PSTN--> toll-free + DIDs claimed to a Traffic Distribution Group (TDG)
                                          |  telephony distribution 100/0 (normal), 0/100 (failover)
             +----------------------------+----------------------------+
             | us-east-1 (primary)        |        us-west-2 (replica) |
             | Connect instance           |  replica (ReplicateInstance): same instance ID,
             |  flows, queues, profiles   |  flows/queues/profiles replicated
             | Lambdas (same names)       |  Lambdas (same names, deployed by pipeline)
             | Lex bot (Global Resiliency replica, same bot ID)                         |
             | DynamoDB global table lfg-caller-cache <------> replica                   |
             | S3 recordings + KMS MRK  --- CRR ---> S3 recordings + KMS MRK replica      |
             | NAT EIP-a (ServiceNow allow list)       NAT EIP-b (also allow-listed)      |
             +----------------------------+----------------------------+
             agents: distribution 100/0 normal; Pune/Monterrey can be pinned per region in drills
```

Active/standby for telephony and agents (warm standby): the replica is fully configured and agents
can log in to either region, but 100 percent of traffic and agents sit in us-east-1 normally. Reason:
one set of real-time metrics and simpler WFM. Note: global routing (active-active cross-region agent
routing) is the default for ACGR instances created on or after 2026-09-01; LFG's instance pair is new,
so we keep it available and decide after the first drill whether to run active-active. The design works
either way; the runbook below shifts distribution, not configuration.

Prerequisites from ACGR requirements: Enterprise Support (LFG has it), SAML 2.0 identity on the
instance, numbers claimed or ported into Connect (not third-party carrier numbers), matching service
quotas in both regions, Lambdas with identical names, and ARNs built with `$.AwsRegion` in flows.

## Telephony and number strategy

- Claim the two toll-free numbers and the 38 ported DIDs to the TDG, not to the instance, so they follow
  the distribution percentage. Numbers on the instance itself do not fail over.
- The two DIDs still at the regional carrier cannot be in the TDG. Mitigation until the port completes:
  carrier-level call forwarding to the main toll-free number, documented as a known gap.
- Avaya coexistence trunk (week 3) terminates in us-east-1 only; trading-floor transfers to the help
  desk use the toll-free number, which then follows the TDG.
- Outbound caller ID numbers are also TDG numbers so callbacks from the replica present the same ID.

## Agents, identity and the desktop

- SAML with Okta using the ACGR global sign-in endpoint, so agents land on whichever region the agent
  distribution sends them to; the custom CCP (Streams) is initialised with the global sign-in URL.
- Agent distribution in 10 percent steps; normal 100/0. In a failover, 0/100. Agents already on calls
  finish them in the primary if it is up; new logins go to the replica.
- Offshore and nearshore teams follow the same distribution; for drills we can move Pune (overnight
  coverage) first, which tests the path with low volume.
- Okta outage (incident 2026-08-29) is not a region problem: logged-in agents keep working; we keep two
  break-glass Connect admin users for emergency console access.

## Regional dependencies and parity

| Dependency | us-west-2 plan | Sync |
|---|---|---|
| Flows, queues, routing profiles, hours | replicated by ACGR | configuration changes made in the primary replicate; pipeline deploys to primary only |
| Lambdas (3) | same names, same code, deployed by the same pipeline stage to both regions | flows reference `arn:aws:lambda:$.AwsRegion:111122223333:function:<name>` |
| Lex bot | Lex Global Resiliency replica (same bot ID), alias in both regions | release pipeline publishes version + alias, replication carries it |
| DynamoDB lfg-caller-cache | global table | multi-region, last writer wins (cache only) |
| Secrets (Okta, ServiceNow OAuth) | Secrets Manager replica secrets | rotation in primary replicates |
| S3 recordings/transcripts | replica bucket via CRR, KMS multi-region key | replication time control for the 15 min RPO |
| ServiceNow | add us-west-2 NAT EIPs to the allow list now | verify quarterly with a synthetic API call from each region |
| Quotas | request matching quotas (concurrent calls, numbers, Lambda concurrency) | checked in the drill checklist |

## Chat and digital channels

Chat does not follow the TDG automatically: the communications widget / StartChatContact endpoint is
per region. The employee portal reads the active chat region from a feature flag (AppConfig) the
runbook flips; flow and instance IDs are the same in both regions, so only the endpoint changes. In-flight
chats in a failed region are lost; the portal shows "start a new chat". RTO 30 min is met by the flag flip.

## Data, recordings and reporting continuity

- Contact records and Contact Lens output are produced in the region that handled the contact. Each
  region streams contact records (Kinesis/Firehose) to S3 in its own region; both land in the data lake
  bucket that is replicated. The weekly KPI pack queries both prefixes.
- RPO: recordings and transcripts replicate within the S3 RTC window (15 min); real-time dashboards are
  per region during an event. Historical metrics for the event window are reconciled after failback.

## Failover decision and runbook

Triggers (any one): Connect health event for us-east-1 affecting inbound calls; synthetic call test fails
3 times in 5 minutes from two carriers; ContactFlowFatalErrors or call failures > 5 percent for 5 minutes.
Decision owner: help desk platform lead (or the incident commander), emergency CAB notified, not consulted.

1. T+0 Declare: incident commander opens bridge, names scribe; check AWS Health and Connect status.
2. T+3 Pre-checks (2 min): replica healthy (log in a test agent via global sign-in), Lambdas in us-west-2
   pass synthetic invoke, Lex alias responds, ServiceNow reachable from us-west-2 NAT.
3. T+5 Shift agents: UpdateTrafficDistribution agent config 0/100 (console or CLI script in the runbook
   repo), message agents via Slack/Teams to refresh the CCP.
4. T+7 Shift telephony: TDG telephony distribution 0/100.
5. T+8 Chat: flip the AppConfig flag to us-west-2.
6. T+10 Verify: synthetic calls to toll-free and two DIDs reach the replica (CTR region), real-time
   metrics in us-west-2 show agents available and calls answered, password reset Lambda succeeds.
7. T+15 Communicate: status page and IT announcement; record times for the regulator file.
Failback: only after 2 hours of primary health; reverse order in 10 percent steps for telephony
(watch error rates at each step), then agents, then chat; reconcile reports.
Rollback of a failed failover: set distributions back to 100/0 (both are reversible API calls).

## Testing and game days

- Twice a year planned drill in a low-volume window (Sunday 07:00 ET), Pune first, then 50/50, then 0/100,
  measure time to 100 percent answered in replica; success = RTO met, no lost calls beyond in-flight.
- Monthly: synthetic call tests to both regions (Connect test cases / external synthetic caller), Lambda and
  Lex synthetic invokes in us-west-2, ServiceNow reachability.
- Every release: pipeline verifies the replica received the flow changes (describe in both regions).

## Cost and operational overhead

The replica has no per-minute cost while idle (Connect is usage-priced); the costs are the ACGR feature
and number charges, Lambda/DynamoDB/S3 replication, and engineering time for parity. Answer to the CFO:
warm costs are mostly storage replication and telephony, a small fraction of one hour of a 210-agent outage.

## Risks and open questions

- Two unported DIDs (carrier forwarding until ported). - Active-active global routing changes WFM and
  reporting: decide after drill 1. - Lambda code drift between regions: one pipeline, one artifact, both
  regions, with a parity check. - ServiceNow allow list maintained by another team: quarterly verification.
- Contact Lens and any AI features must be available in us-west-2 for the same configuration; check per
  feature before relying on them in failover.
