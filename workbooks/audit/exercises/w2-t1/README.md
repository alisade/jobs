# audit/w2-t1 - The CM-03 population does not reconcile: 38 vs 421

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Wed: population completeness and accuracy, API pagination)

## Scenario

MFH internal audit (fictional) extracts the CM-03 population for the monorepo `mfh/tms-core` from
the GitHub Enterprise REST API and reconciles it to DeployHub's production deploy log. The external
auditor has rejected the H1 2026 file: **38 changes in the population, 421 in the deploy log.** The
export job exits 0 with no errors. The team chat blames the time-zone filter, a lost token scope
and last weekend's GHE upgrade. Nothing ControlPilot concluded on H1 samples can be used until this
is explained, and the auditor wants the explanation in IPE terms (how do you know the extraction is
complete?).

The API is an in-process fake (`popexport/fakeapi.py`) that behaves like the real endpoint. No network.

## What you have

| Path | What it is |
|---|---|
| `popexport/client.py` | the PR listing client |
| `popexport/population.py` | population build and reconciliation to the deploy log |
| `popexport/fakeapi.py` | the API stand-in (do not edit) |
| `export.py` | `make export` runs the extraction and writes `incident/export.log` and `incident/reconciliation.json` |
| `incident/` (after `make setup`) | the export log with request-level debug lines, the reconciliation, the auditor's e-mail, the chat thread |

## Your task

1. `make setup`, then read `incident/`. Reproduce with `make export`.
2. Find the root cause and prove it from the log (which requests were made and what came back).
   Rule each chat theory in or out with evidence.
3. Fix the client so the extraction is complete no matter what page size the server enforces, and
   so it cannot loop forever on a misbehaving server.
4. `ANSWER.md`: root cause with evidence, fix and verification, and the paragraph you would send the
   auditor (what went wrong, how completeness is now demonstrated, what control you added so a
   short extraction cannot pass silently again).

## Acceptance criteria (what the grader checks)

- The population reconciles to the deploy log (421 = 421).
- Every PR is fetched for several server caps and requested page sizes, with the expected number of requests.
- Exact multiples of the page size and empty repositories work; a pagination loop is bounded.
- The time-zone filter is unchanged (it was correct).
- `ANSWER.md` names the root cause with log evidence and rules out the red herrings.

## How to run

```bash
make setup     # venv + incident/
make export    # reproduce
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w2-t1
make clean
```
