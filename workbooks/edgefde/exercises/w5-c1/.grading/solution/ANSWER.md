# ANSWER: edgefde/w5-c1 OTA model rollout with canary and automatic rollback

## Approach

Modelled the rollout as a persisted state machine first (what must survive a crash), then wrote the
per-window loop: top up the batch, tick, gate every touched device, advance or roll back.

## Fix

Cumulative phases 1 / 20% / 50% / 100% with a soak of three healthy windows per device. Gates: process
up, inference error rate, p95 latency and alert rate against three times the pre-rollout baseline,
because a model can be "healthy" as a process and still flood the planners with alerts. Any failure
rolls back every touched device, not only the current batch. Offline devices wait up to six windows,
then are skipped back to the old model and reported. State is written atomically after each window,
so a restarted controller continues the same rollout and never updates a device twice.

## Trade-offs / what I would do in production

On AWS this maps to IoT Jobs with a rollout config and an abort config on failure thresholds, or a
Greengrass deployment of the model component; Mender phases on Linux images; Argo Rollouts if the
gateways run k3s. I would pick one canary per hardware revision, since the rev2 failure only showed in
the last phase. Alert rate is a proxy; confirmed outcomes from work orders should feed the champion
decision later. A rollback pages the on-call reliability engineer with the reason.
