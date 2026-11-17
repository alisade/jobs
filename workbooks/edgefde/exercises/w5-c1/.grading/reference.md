# Reference: edgefde/w5-c1

The reference controller is `.grading/solution/fleet/rollout.py` (about 150 lines).

- State is one JSON document (status, order, cumulative phase counts, phase index, touched, skipped,
  per-device healthy streaks and offline counters, baseline alert rate), written via a temp file and
  `os.replace` after every window, so a crash never leaves half a file and a new controller simply
  continues the loop.
- Each window: top up the current phase up to `max_concurrent` devices that have been told the new
  version but not yet reported it; tick; gate every touched device that reports the new version.
  The first failure rolls back every touched device and waits for convergence.
- Offline: counted per device, reset when it reports; after the timeout the device is skipped and
  its desired version reset to the old model, so it does not wake up on an unvetted one.
- The rev2-only failure shows why a canary of one is not enough on a mixed fleet: in production pick
  one canary per hardware revision (or per site), which here would have caught `v7-rev2bad` in phase 0.

Production mapping: AWS IoT Jobs (job rollout config with exponential rate, abort config with failure
thresholds, timeouts per execution), Greengrass v2 deployments for model components, Mender deployment
phases, or Argo Rollouts on k3s gateways. Health = device telemetry; model quality gates should also
use confirmed outcomes once they arrive, not only alert rate.
