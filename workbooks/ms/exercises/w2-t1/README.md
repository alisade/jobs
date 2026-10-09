# ms/w2-t1: Live fleet dashboard flat since 09:40

Type: troubleshooting. Estimate: 1.5-2 h. Exam: DP-700 - Ingest and transform data (30-35%): streaming; Monitor and optimize (30-35%): identify and resolve errors (Eventstream, Eventhouse).

## Scenario

Contoso Fleet's telemetry gateway publishes one JSON event per vehicle every 20 seconds to a Fabric
Eventstream. The Eventstream has two destinations: the `fleet` KQL database in the `eh-fleet`
Eventhouse (table `TelemetryLanding`, JSON ingestion mapping `TelemetryLanding_mapping`) and a raw
copy in lakehouse `lh_fleet_raw`. An update policy fills `TelemetryEnriched`, which the FleetOps Live
dashboard and the Activator "Engine overheating" rule read.

You are the data-platform on-call. This arrived at 10:07 UTC:

> [P2] FleetOps live dashboard - no data.
> "The live fleet map and the speed tiles have been flat since about 09:40. Vehicles are definitely
> moving (drivers are calling in). The overheating alerts have also gone quiet, which is scary.
> Eventstream page shows events flowing, so I don't think it's the trucks."

## Your task

1. `make setup` builds the evidence bundle in `incident/`: the pager text, Eventstream metrics, KQL
   query results you ran, the Eventstream data preview, capacity metrics, the Activator status and a
   git log from the gateway repo.
2. Find the root cause. Not everything in the bundle is relevant.
3. Fix the Eventhouse artifacts in `eventhouse/` (they are what the deployment script applies). Use
   `make replay` to push the Eventstream preview through *your* mapping file and see what would land.
4. Write `ANSWER.md`: root cause with evidence (quote file names and lines), the fix and how you
   verified it, what happens to the rows that landed between 09:40 and the fix, and what you would
   change so this cannot page someone again.

## Acceptance criteria

- Events from the current gateway land in `TelemetryLanding` with every column populated and correct
  (types, timestamp precision).
- The mapping stays a valid Kusto JSON mapping: `Column`, optional `DataType`, `Properties` with
  `Path`/`Transform`, every table column mapped once, documented transforms only, no constants.
- The update policy still runs, still filters bad rows, and is still transactional. Do not "fix" the
  dashboard by weakening data quality.
- `ANSWER.md` has `## Approach`, `## Root cause`, `## Fix`, `## Trade-offs / what I would do in production`.

## How to run

```
make setup    # uv venv + generate incident/
make replay   # incident/eventstream_data_preview.jsonl through eventhouse/mappings/TelemetryLanding_mapping.json
make test     # visible checks
make clean    # removes .venv and incident/ (your edits in eventhouse/ stay)
```

`scripts/sim.py` is a local stand-in for JSON ingestion with a mapping. Like the real engine, a path
that does not exist produces `null`, not an ingestion error. Supported JSONPath subset: `$.a.b`,
`$['a b']`, `$.a[0]`. Grade from the workbooks root: `/grade ms/w2-t1`.

## What to submit

Your changes under `eventhouse/` and `ANSWER.md`. Do not edit `scripts/` or `tests/`.

## Study guide links

- [Week 2 Mon - Real-Time Intelligence and Eventstream](../../../../microsoft-adf-powerapps-study-plan.html#week2)
- [Week 3 Thu - Identify and resolve errors](../../../../microsoft-adf-powerapps-study-plan.html#week3)
- [JSON mapping](https://learn.microsoft.com/en-us/kusto/management/json-mapping?view=microsoft-fabric) /
  [Mapping transformations](https://learn.microsoft.com/en-us/kusto/management/mappings?view=microsoft-fabric)
- [.alter ingestion mapping](https://learn.microsoft.com/en-us/kusto/management/alter-ingestion-mapping-command?view=microsoft-fabric)
- [Update policy](https://learn.microsoft.com/en-us/kusto/management/update-policy?view=microsoft-fabric) /
  [.show ingestion failures](https://learn.microsoft.com/en-us/kusto/management/ingestion-failures?view=microsoft-fabric)
- [Eventstream: Eventhouse destination](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-destination-kql-database)
