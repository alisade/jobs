# Reference: ms/w3-t1 PROD gold table stale, pipeline green

## Root cause
PR #412 renamed the gold notebook (`nb_load_gold` -> `Load Gold Sales`). The `find_replace` entries in
`workspace/parameter.yml` that swap the DEV workspace id and lakehouse ids inside notebook definitions were
filtered by `item_name`, which is the case-sensitive display name. Per fabric-cicd docs a non-matching filter
skips the replacement for that file; no error is raised for a literal find_value with zero matches. The PROD
notebook was therefore published with `default_lakehouse`, `default_lakehouse_workspace_id` and
`known_lakehouses` pointing at DEV. The scheduler identity is a member of both workspaces, so the PROD pipeline
reads DEV silver and writes DEV gold successfully. Every run is green; PROD gold is frozen at Tuesday.

The pipeline's `key_value_replace` entry was updated in the same PR only because `$items.Notebook.nb_load_gold.$id`
fails validation loudly. That asymmetry (loud vs silent) is the interview point.

## Evidence chain
1. PROD Delta history: last commit 2026-10-06 06:05 (v391).
2. Monitoring hub: gold notebook Succeeded Wed-Fri.
3. Driver log Thu: `Committed delta #388 to abfss://<DEV ws>@onelake.../<DEV lh_gold>/Tables/sales_daily`.
4. DEV history: v387-389 at 06:05 with PROD volumes beside DEV's 04:31 sample runs.
5. Release log: only two find_replace replacements, both in nb_load_silver.
6. `make render ENV=PROD`: gold notebook META still holds DEV GUIDs.

Red herrings: Tuesday capacity throttling (delay, not redirection) and the ExecutorLostFailure/GC warning
(task retried and stage finished; commit logged).

## Fix (see solution/)
- parameter.yml: filter by `item_type: "Notebook"` only. The find_values are DEV-only GUIDs so global matching
  is safe; `file_path: "**/notebook-content.py"` is an acceptable alternative. Updating `item_name` to the new
  name passes most tests but fails `test_fix_survives_the_next_rename` by design.
- deploy/check_bindings.py: GUID scan against targets.json, any GUID owned by another environment is a leak,
  `.platform` excluded, unknown GUIDs ignored, exit 1 on leaks. Run it in CI between a dry-run render and publish.
- Data: rerun PROD for 10-07..10-09; clean PROD rows from DEV (or RESTORE DEV sales_daily to v386).

## Alternatives
- Fabric deployment pipelines + deployment rules (default lakehouse rule for notebooks) instead of fabric-cicd.
- Runtime binding: pass workspace/lakehouse ids as notebook parameters from the pipeline and use abfss paths, or
  `%%configure` with `defaultLakehouse` {name, id, workspaceId}; then the definition has no environment GUIDs.
- Least privilege: one scheduler identity per environment with no access to DEV would have made this fail loudly.

## Interview angles
- "Your pipeline is green but the data is stale. What do you look at first and why?" (freshness of the sink,
  not the run status).
- "Why is a silently skipped replacement worse than a failed deployment, and how do you design for that?"
