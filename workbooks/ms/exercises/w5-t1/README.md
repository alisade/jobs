# ms/w5-t1: FieldOps 1.4 release to UAT fails at import

Type: troubleshooting. Estimate: 1.5-2 h. Exam: AB-400 - Build solutions (15-20%): implement ALM (solutions, dependencies, layering, pipelines).

## Scenario

Contoso Field Services builds two Dataverse solutions under the `contoso` publisher: **ContosoCore** (shared
tables such as Asset, Site, Region, owned by the platform team, released by its own `core-build` pipeline) and
**FieldOps** (work orders, dispatch app, technician forms). Source control holds the unpacked solutions
(`pac solution unpack`); GitHub Actions packs them, and a release workflow imports the managed zips listed in
`deploy/manifest.yaml` into the target environment with `pac solution import`.

Message from the FieldOps lead, Thursday 2026-10-08 15:31:

> The UAT release of FieldOps 1.4.0.0 failed at the import step, and a manual retry in the maker portal fails
> too. UAT sign-off is tomorrow 10:00. QA thinks it is the unmanaged change they made on the Account form in UAT,
> someone else blames the solution checker warnings, and the team wants to rerun with
> `--skip-dependency-check`. Can you find out what is actually wrong and fix the release properly?

`make setup` generates `incident/` with the workflow log, the import job record, the maker portal retry, solution
inventories for DEV and UAT, the component layers of the Account main form in UAT, and the chat thread.

## Your task

1. Find the root cause and prove it from `incident/` and the unpacked solution under `solutions/FieldOps/`.
2. Fix the release so FieldOps 1.4.0.0 imports into UAT, without removing the 1.4 feature and without
   shipping unmanaged solutions to UAT.
3. Implement the preflight `deploy/preflight.py` (contract below) so the release workflow can fail fast with a
   readable message before calling `pac solution import`.
4. In `ANSWER.md`, also explain the Account form "Active" layer QA mentioned: what it is, whether it blocks this
   import, what it does to future releases, and what you would do about it.

### Preflight

- `parse_version("2.1.0.0") -> (2, 1, 0, 0)`; 2-4 numeric parts, padded to 4; `ValueError` otherwise.
- `missing_dependencies(solution_xml) -> list[dict]` from `<MissingDependencies>` (keys in the docstring).
- `preflight(manifest, inventory, artifacts, solution_xml_by_name) -> list[str]` walks the manifest **in order**
  against the target inventory, updating the simulated inventory after each step, and reports a message for:
  - an artifact that is not in `artifacts.json`, or whose solution/version/managed flag differs from the step;
  - a downgrade below the version installed in the target;
  - managed over an unmanaged solution of the same name (or unmanaged over managed);
  - each `MissingDependency` of that solution whose required solution is not present at the required version or
    higher at that point in the sequence (messages name the required solution and version);
  - any dependency on the `Active` solution (an unmanaged component that no solution carries).
- CLI (`make preflight`): prints one `PREFLIGHT FAIL ...` line per problem, exits 1 on problems, 0 otherwise.

## Acceptance criteria

- Simulating the manifest against `deploy/environments/uat.json` and `deploy/artifacts.json` succeeds.
- FieldOps 1.4.0.0 is still shipped managed with its Region Code form control and view column intact;
  `Solution.xml` is not hand-edited to hide dependencies; no `--skip-dependency-check` / force-overwrite tricks.
- `deploy/preflight.py` meets the contract above and passes on your fixed manifest.
- `ANSWER.md`: root cause with evidence, the fix and how you verified it, and the layering explanation.

## How to run

```
make setup        # uv sync + generate incident/
make test         # visible tests
make preflight    # run your preflight against the UAT manifest
make clean
```

## What to submit

Your changes under `deploy/` and `ANSWER.md`. Then run `/grade ms/w5-t1` from the workbooks folder.

## Study guide links

- [Week 5 Fri - Solutions and ALM concepts](../../../../microsoft-adf-powerapps-study-plan.html#week5)
- [Week 5 Weekend - Pipelines, CI/CD, architecture choices](../../../../microsoft-adf-powerapps-study-plan.html#week5)
- [Solution concepts](https://learn.microsoft.com/en-us/power-platform/alm/solution-concepts-alm)
- [Solution layers](https://learn.microsoft.com/en-us/power-platform/alm/solution-layers-alm)
- [Dependency tracking for solution components](https://learn.microsoft.com/en-us/power-platform/alm/dependency-tracking-solution-components)
- [Organize your solutions (segmentation, multiple solutions)](https://learn.microsoft.com/en-us/power-platform/alm/organize-solutions)
- [Troubleshoot missing dependencies on solution import](https://learn.microsoft.com/en-us/troubleshoot/power-platform/dataverse/working-with-solutions/missing-dependency-on-solution-import)
- [pac solution reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution)
