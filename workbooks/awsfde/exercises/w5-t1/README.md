# awsfde/w5-t1 - Acme's product shows a supplier it never used

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 5 (Mon: graph modeling; Wed: Neptune Analytics loading; Thu: a tenant-safe graph tool)

## Symptom

Acme Foods' supply planning lead reports that Tidewater Ask lists two medical suppliers for their
pasta, and that their real suppliers are missing. Duplicates appear too. It was fine yesterday.
Brightline Health's graph was onboarded into the same Neptune Analytics graph the day before. Read
`evidence/TICKET-5611.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/TICKET-5611.txt`, `evidence/onboarding-brightline.md` | the ticket and the onboarding runbook as executed |
| `evidence/neptune-load-format-note.md` | the relevant lines of the openCypher load format docs |
| `evidence/questions.jsonl` | the questions in the ticket |
| `data/source/*.json` | each tenant's ERP extract (the export job's input) |
| `export_job/export.py` | writes each tenant's openCypher load files |
| `export_job/validate.py` | the pre-load validator (ASK-377), not implemented yet |
| `graph_tool/query.py` | the `suppliers_of_product` tool's openCypher template |
| `neptune_sim/loader.py` | a local stand-in for bulk loading into one shared graph (see its docstring). Treat it as the environment, not the suspect. |
| `run/` | created by `make setup`: `load/` (the CSVs that were loaded), `load-jobs.log`, `query.log`, `summary.txt` |

## Your task

1. Find the root cause and prove it with the load files, the load job statistics and the query log:
   why Acme sees Brightline's suppliers, why its own suppliers disappeared, and why the smoke test
   and Brightline did not notice.
2. Decide whether the duplicate rows (CS-5480) are related.
3. Fix the export so this cannot happen again, implement the pre-load validator so a load like this is
   rejected before it touches the graph, and make the tool query safe even when bad data is present.
4. Verify with `make test` and `make replay` (the replay rebuilds the graph from the load history).
5. Write `ANSWER.md`: root cause, evidence, exposure in both directions, how you would repair the real
   graph, and prevention.

## Acceptance criteria (what the grader checks)

- Exported node and relationship IDs are tenant-scoped; no ID is exported by two tenants.
- The validator rejects id collisions with another tenant's vertices, cross-tenant or unknown
  endpoints, duplicate ids and rows with the wrong `tenant_id`; it accepts clean loads and reloads.
- Replaying the load history completes both loads with no node updated by another tenant's load.
- The tool query returns only the caller's tenant, once per supplier, even with a planted
  cross-tenant relationship.
- `ANSWER.md` explains the mechanism with evidence and separates the red herring.

## How to run

```bash
make setup     # shared venv + replay of the load history and the questions into run/
make test
make replay    # after your fix
# from workbooks/: /grade awsfde/w5-t1
make clean
```
