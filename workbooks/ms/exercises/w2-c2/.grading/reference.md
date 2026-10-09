# Reference: ms/w2-c2

Reference JSON: `.grading/solution/pl_nightly_orchestrator.DataPipeline/pipeline-content.json`.

## Key points

- **Dependency conditions.** `Succeeded`, `Failed`, `Skipped`, `Completed`. Multiple dependencies are
  AND-ed; multiple conditions on one dependency are OR-ed. A downstream activity of a failed activity
  on the `Succeeded` path is *skipped*, which is why the run would end Succeeded if you only had a
  "Upon failure" branch that itself succeeds: the Fail activity is what forces the run to Failed.
- **Until.** Evaluates the expression after each iteration (do-until), so the inner activities always
  run at least once. `timeout` (D.HH:MM:SS) bounds the loop; reaching it fails the Until activity.
  Stop on every terminal state or a `Failed` export polls until the timeout.
- **Set variable scope.** Variables are pipeline-scoped; setting one inside a parallel ForEach races.
  Use a sequential loop, pass values as child pipeline parameters, or use child pipeline return values.
- **ForEach.** `isSequential: false` with `batchCount` (max 50; default 20). `@item()` is only valid
  inside the loop.
- **Invoke pipeline.** New activity supports cross-workspace and ADF/Synapse pipelines through a
  connection and lets you monitor the child; legacy only same-workspace. `waitOnCompletion: true` is
  needed for child failures to fail the parent activity.
- **Policies.** Default activity timeout is 12 hours; set short timeouts on external calls. Control
  activities have no retry.

## Interview angles

- The partner API sometimes returns HTTP 202 with no body for 30 s. How does that affect
  `activity('web_start_export').output.exportId`, and how would you guard it?
- How would you rerun only the failed regions? (Rerun from failed activity in the Monitoring hub, or
  pass a region list parameter.)
- When would you move this orchestration to an Apache Airflow job in Fabric instead?
