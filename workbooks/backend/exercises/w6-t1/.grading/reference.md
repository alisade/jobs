# Reference: backend/w6-t1 Lead workflows stuck after Tuesday's deploy

Injected faults (both from PR #812 in `keystone_workflows/lead_workflow.py`):
1. A new activity (`enrich_lead`) inserted before `propose_owner` without a version guard: replaying any
   history recorded by 2026.44 fails with a nondeterminism error (TMPRL1100), so signals to those
   executions never take effect.
2. `datetime.now()` in workflow code for `sla_deadline`, with the sandbox disabled to silence the
   sandbox's RestrictedWorkflowAccessError: the value changes on every replay (visible with
   `max_cached_workflows=0`, or whenever the worker evicts the workflow from its cache).

Red herring: `enrich_lead` StartToClose timeouts on new executions are retried activities.

Fix: `.grading/solution/keystone_workflows/lead_workflow.py` (workflow.patched, workflow.now(), sandbox
on) and the model answer in `.grading/solution/ANSWER.md`.

How the histories were made: `.grading/authoring/record_histories.py` runs the 2026.44 workflow
(`.grading/authoring/v1_workflow.py`, same workflow type name) on the time-skipping server, stops four
executions at different points, and writes `histories/*.json`. Re-run it only if the models change.

## Interview angles
- "Why does Temporal require determinism at all?" (State is rebuilt by replaying the event history; the
  code must produce the same commands for the same history.)
- "patched vs worker versioning?" (patched for small changes, branches live in code until old runs close;
  worker build-id versioning pins executions to the code they started on, better for big rewrites.)
- "What else is nondeterministic in Python workflow code?" (random, uuid4, wall time, iterating a set,
  network or DB calls, threads, reading env vars or config files at runtime.)
