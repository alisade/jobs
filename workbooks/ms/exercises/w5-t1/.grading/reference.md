# Reference: ms/w5-t1 FieldOps 1.4 release to UAT fails at import

## Root cause
FieldOps 1.4.0.0 added a form ("Asset - Field Ops", component type 60) and a view ("Assets by Region", type 26)
on the Core table `contoso_asset` that use the column `contoso_regioncode` (type 2). That column belongs to
ContosoCore and was introduced in ContosoCore 2.1.0.0. When FieldOps was exported, Dataverse wrote both
requirements into `<MissingDependencies>` in Solution.xml with `solution="ContosoCore (2.1.0.0)"`. UAT has
ContosoCore 2.0.3.0 and the manifest imports only FieldOps, so the import fails with "The following solution
cannot be imported: FieldOps. Some dependencies are missing." (maker portal: "Import failed due to missing
dependencies.").

## Fix
Import ContosoCore 2.1.0.0 managed (upgrade) before FieldOps 1.4.0.0 managed. Reference files:
`solution/deploy/manifest.yaml`, `solution/deploy/preflight.py`.

Wrong fixes the tests reject:
- deleting the control/view column or the MissingDependency entries (removes the feature; a re-export brings
  them back);
- importing an unmanaged Core or FieldOps into UAT;
- `--skip-dependency-check` (applies to product-update dependencies only) or force-overwrite.

## Layering (red herring)
The Account main form in UAT has layers System (managed) < ContosoPortal 3.2.1.0 (managed) < Active (unmanaged).
The Active layer is on top and is what users see. It does not block FieldOps (no overlap), but every future
managed update of the Account form will be masked by it. Remove it ("Remove active customizations" on the
component layer) after moving the change into source. Managed solutions layer in import order; the unmanaged
Active layer is always on top.

## Preflight design notes
Simulate the manifest in order and update the simulated inventory after each step; compare 4-part numeric
versions; treat `solution="Active"` as an error (unmanaged dependency that no solution carries); validate the
artifact matches the step (solution, version, managed). This is cheap and catches the incident before
`pac solution import`. Power Platform Pipelines run a similar dependency validation before deploying.

## Interview angles
- "When would you put a column in Core versus in the feature solution, and how do you release them?"
- "A tester changed a form in UAT. What does that do to your next managed release and how do you clean it up?"
