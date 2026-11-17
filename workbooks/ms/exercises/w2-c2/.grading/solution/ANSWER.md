# ms/w2-c2 ANSWER

## Approach
- Linear happy path on `Succeeded`: notebook, start export, Until, If condition, ForEach. Each risky step has its own `Failed` branch into a Fail activity with a distinct errorCode, so the run status is Failed and the alert can route on the code.
- Until stops on `Completed` OR `Failed`; a hung export hits the 1 h Until timeout, which surfaces as the Until activity failing, so `fail_export_timeout` hangs off `Failed`. The If condition then turns a partner-reported `Failed` into `EXPORT_FAILED`.
- Inside the Until: GET, Set variable from `activity('web_get_export_status').output.status`, then Wait 60 s. The Set variable is safe because the Until is sequential; inside the parallel ForEach I set no variables.
- ForEach runs `invoke_region_load` in parallel with batchCount 3 and `waitOnCompletion: true`, otherwise child failures never propagate and `fail_region_loads` could never fire.
- Policies: notebook retry 2 at 120 s with a 2 h timeout (Spark session start-up failures are transient); start export retry 3 at 30 s and a 10 min timeout (default 12 h would hold a run open). No retries on control activities.

## Fix
I would ask the partner for an idempotency key on `POST /v1/exports`: with retry 3 a timeout after the partner accepted the request can create a second export.

## Trade-offs / what I would do in production
- Polling costs a few activity runs per minute; a webhook activity with a callback would be cheaper but needs the partner to call back into Fabric.
- batchCount 3 matches the capacity (F16) and the child pipelines' Copy parallelism; raise it only after checking the Capacity Metrics app.
- Retry only idempotent work, or make it idempotent (MERGE in the notebook, export idempotency key).
- Test: lint in CI, run in the dev workspace with `env=dev` against the partner sandbox, then promote through the deployment pipeline with a rule that swaps the connection.
