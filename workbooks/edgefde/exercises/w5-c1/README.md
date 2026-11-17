# edgefde/w5-c1 - OTA model rollout with canary and automatic rollback

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Mon: OTA approaches; Tue: rollout strategy, canary and rollback; Wed: offline devices)

## Scenario

Corvane Industrial's Dunmore plant (fictional) now has ten edge gateways, `gw-01`..`gw-10`, each
running the pump-health model as a separate file from the application, so a new model can ship
without rebuilding anything. Until now someone copied the new model to every gateway by hand on a
Sunday. Last month a model that crashed on the newer rev2 CPU boards (`gw-07`..`gw-10`) took four
gateways offline for a day before anyone noticed.

The reliability lead wants a rollout controller that behaves like the canary rollouts you know from
Kubernetes, but for devices on a plant network that drop off now and then: one canary, then batches,
health gates on every window, automatic rollback of every touched device on the first bad sign, and
offline gateways that neither block the fleet forever nor count as failures. It must survive its own
restart halfway through.

`fleet/sim.py` (complete, read its docstring) is an in-process fleet with a fake clock: one `tick()`
is one scoring window; `set_desired(device, version)` is applied on the next tick if the device is
online. `MODELS` defines how each version behaves, including bad ones.

## What you have

| Path | What it is |
|---|---|
| `fleet/sim.py` | simulated fleet, health reports, fault injection (do not edit) |
| `fleet/rollout.py` | `Policy`, `RolloutReport`, `RolloutInProgress` and the controller stub (implement) |
| `scripts/rollout.py` | `make rollout V=v7` (try `v7-crash`, `v7-storm`, `v7-slow`, `v7-rev2bad`, `--offline gw-05:40`) |

## Your task

Implement `RolloutController(fleet, state_path, policy)`:

- `start(from_version, to_version)`: refuse with `RolloutInProgress` if the state file holds a rollout
  that is still `in_progress`. Take one window of reports as the baseline (median `alert_rate` of
  devices on `from_version`). The canary is the first **online** device in id order; the rest follow
  in id order. Phase sizes are cumulative: an int is a device count, a float a fraction of the fleet
  (rounded up). With the default policy and 10 devices: 1, 2, 5, 10.
- `run(max_windows=500)`: one loop iteration = one `fleet.tick()`. Per iteration:
  - give the new version to devices of the current phase, never more than `max_concurrent` devices
    that have not yet reported running it;
  - check every touched device's report: down, `error_rate > max_error_rate`, `p95_ms > max_p95_ms` or
    `alert_rate > max_alert_ratio x max(baseline, 0.005)` is a failure: set every touched device back
    to `from_version`, tick until they report it (up to `rollback_timeout_windows`), status
    `rolled_back`, `failed_phase` = the phase index, `reason` names the device and the gate
    (use the words "down", "error rate", "latency" or "alert");
  - an offline device is not a failure; after more than `offline_timeout_windows` consecutive
    offline windows it is skipped: its desired version goes back to `from_version` and it is listed
    in `skipped_offline`;
  - a phase is done when every device in it is skipped or has `healthy_windows` consecutive healthy
    reports on the new version; after the last phase the status is `succeeded`.
  - Save the state to `state_path` (JSON, atomically) after every iteration. If `max_windows` runs out,
    return status `in_progress`; a new controller on the same state file continues where it stopped
    without restarting the rollout.
- `report()`: the `RolloutReport` (`updated` lists touched, not skipped devices when not rolled back).

## Acceptance criteria (what the grader checks)

- Good model: canary first, next device only after the canary soaked, all ten on the new version.
- Crash, alert storm and latency regressions stop at the canary; only the canary ever got them.
- `v7-rev2bad` passes the canary and fails when the rev2 boards join (phase 3): everything touched
  goes back to v6.
- `max_concurrent` honoured; short outages wait, long outages are skipped; an offline canary candidate
  is passed over.
- Resume after a controller crash (no device updated twice), also on the failure path; no two
  rollouts at once; state file is JSON with the status.
- `ANSWER.md` maps your design to a real OTA system and explains your gate choices.

## How to run

```bash
make setup
make rollout V=v7-rev2bad
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w5-c1
make clean
```

## What to submit

`fleet/rollout.py` and a filled-in `ANSWER.md`.
