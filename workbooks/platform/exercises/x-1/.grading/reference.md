# Reference: platform/x-1

A strong model answer is in `.grading/solution/DESIGN.md` and `.grading/solution/ANSWER.md`.
Points a grader should look for are in the rubric. Facts to check against the learner's text (verify
against current GKE docs when grading, since limits change):

- Release channels: Rapid, Regular, Stable, Extended. "No channel" is deprecated. Prod on Stable with
  dev/stg on Regular gives a natural soak; Extended trades features for a longer support window.
- Maintenance windows must provide a minimum amount of availability over a rolling period, so a
  window cannot be made arbitrarily small; exclusions are the tool for freezes. A "no upgrades"
  exclusion has a short maximum length (about 30 days); "no minor upgrades" and "no minor or node
  upgrades" can last much longer (up to the version's end of support).
- Surge upgrades respect PDBs for a limited time (about an hour) before draining anyway, which is
  exactly what happened to the singleton in INC-3982.
- Blue-green node pool upgrades keep the old pool during soak, so rollback is cheap, but they need
  the full pool's capacity and quota again.
- Control plane minor upgrades cannot be downgraded by the customer; node pools can be rolled back.
- Quota arithmetic: us-central1 N2_CPUS 480 limit, 400 used -> 80 free; blue-green of
  pool-default-v2 needs 144 -> request quota (2-5 business days) or use surge with maxSurge 3.
