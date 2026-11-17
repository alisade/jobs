# SUP-8812  Pipeline view shows an account that is not ours  (priority: P2, security review requested)

Reporter: Dana Whitfield (sales ops, bu-amer)   Opened: 2026-11-06 09:12 PT

> On my pipeline, "Cedar Grid platform" (our deal) shows the account as **Fjordline AS**. We do not
> have a Fjordline account in Americas; I think that is an EMEA customer. A refresh a few minutes later
> showed Cedar Grid Inc again. Two of my reps saw the same thing yesterday afternoon on other deals.
> The agent assistant also answered "the Cedar Grid deal is with Fjordline AS" when I asked it.

Support notes (L2, Jonas):
- Could not reproduce from a fresh browser session at 09:40.
- Suspect the CDN is caching the GraphQL response between users. Asked the edge team to check
  Cache-Control on /graphql.

Edge team reply (10:05): /graphql responses carry `cache-control: private, no-store`; the CDN logs show
POST /graphql as pass-through (never cached). Sending it back to the pipeline read layer team.

Also reported since Tuesday (sprint 44 deploy):
- bu-emea rep: renamed "Orbital Freight" to "Orbital Freight Group" in accounts, the pipeline view
  kept showing the old name until the pod restarted on Wednesday night.
