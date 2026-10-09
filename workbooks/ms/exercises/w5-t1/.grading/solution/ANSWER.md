# ANSWER: ms/w5-t1 FieldOps 1.4 release to UAT fails at import

## Approach
Read the workflow log first. Solution checker passed its threshold (2 Medium Xrm.Page findings, threshold High),
so it did not stop the job. The failure is the import itself:

    Solution manifest import: FAILURE: The following solution cannot be imported: FieldOps. Some dependencies
    are missing. The missing dependencies are : <MissingDependencies><MissingDependency ...><Required type="2"
    schemaName="contoso_regioncode" ... parentSchemaName="contoso_asset" ... solution="ContosoCore (2.1.0.0)" />
    <Dependent type="60" ... displayName="Asset - Field Ops" .../> ...

The maker portal retry says the same ("Import failed due to missing dependencies", Managed Solutions:
ContosoCore (2.1.0.0)). `solutions/FieldOps/src/Other/Solution.xml` lists three MissingDependency entries; two
require ContosoCore 2.1.0.0 (Region Code column, type 2, needed by the form type 60 and view type 26 added in 1.4)
and one requires ContosoCore 2.0.0.0 (the Asset table). `pac-solution-list-uat.txt` shows ContosoCore 2.0.3.0 in
UAT, while DEV has ContosoCore 2.1.0.0 (unmanaged). The manifest imports only FieldOps.

## Root cause
FieldOps 1.4.0.0 depends on the column `contoso_regioncode` on `contoso_asset`, which ships in ContosoCore
2.1.0.0. UAT has ContosoCore 2.0.3.0 and the release manifest does not import ContosoCore 2.1.0.0 before
FieldOps, so Dataverse rejects the import because a required component exists neither in the solution nor in
the target. Core 2.1.0.0 was built (core-build #1187, 2026-10-02) but never released to UAT.

Red herrings:
- The Account main form has an unmanaged (Active) layer in UAT on top of ContosoPortal and System. That is an
  unmanaged customization made directly in UAT. It does not block this import (FieldOps does not touch the
  Account form). But the Active layer always sits on top and wins: future managed updates to that form from
  ContosoPortal will import fine and stay invisible. Fix: move Jordan's change into source (Portal or a solution
  in DEV), then remove the active layer in UAT ("Remove active customizations"), and stop making changes in UAT
  (managed environment, maker permissions).
- Solution checker Xrm.Page warnings: real tech debt, not related to the import.
- `--skip-dependency-check` only skips dependencies flagged as product updates; it would not create the missing
  column and is not a fix.

## Fix
- `deploy/manifest.yaml`: import ContosoCore 2.1.0.0 managed (`ContosoCore_2_1_0_0_managed.zip`, upgrade over
  2.0.3.0) first, then FieldOps 1.4.0.0 managed.
- `deploy/preflight.py`: simulates the manifest in order against the target inventory and the MissingDependencies
  in Solution.xml. On the original manifest `make preflight` prints
  `PREFLIGHT FAIL FieldOps 1.4.0.0: requires ContosoCore >= 2.1.0.0 for contoso_regioncode on contoso_asset ...`
  and exits 1; on the fixed manifest it prints `preflight: 0 problem(s)` and exits 0.
- Tomorrow: confirm with the platform team that Core 2.1.0.0 is approved for UAT (it also changes Core for any
  other consumer, e.g. ContosoPortal), run the release, smoke test the Asset form and the Assets by Region view.

## Trade-offs / what I would do in production
- Make the dependency explicit: the release manifest (or Power Platform Pipelines) deploys the Core version the
  FieldOps build was compiled against; preflight runs before every import.
- Version Core and FieldOps independently but record the minimum Core version in the FieldOps build output.
- Avoid adding Core columns from the FieldOps team's environment work; request them through Core.
- Block unmanaged changes in UAT/PROD (managed environments, no system customizer for testers).
