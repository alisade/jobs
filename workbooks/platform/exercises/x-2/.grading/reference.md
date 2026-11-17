# Reference: platform/x-2

Injected fault: `argocd/applicationsets/riq-api-stable.yaml` has `targetRevision: '>=2.0.0'`. Helm
(Masterminds semver) resolves a range to the highest matching release, so the range meant "newest
release from 2.0.0 up", including 3.x. Pre-releases are excluded, which is why 3.0.0-rc.1 (11-06)
did not trigger it; 3.0.0 published 15:02:41 did, at the next periodic refresh (15:06).

Red herring: selfHeal (commit 9b20d7f). It reverts live drift; versions come from the desired
state. Automated sync (on since June) applied the new desired state; without it prod would have
sat OutOfSync.

Reference fix: `.grading/solution/argocd/applicationsets/riq-api-stable.yaml` pins `2.4.1`.
Bounded alternatives `~2.4`, `2.4.*`, `>=2.4.0 <3.0.0` also pass. Fixes that break the grader's
guards: renaming the generated Applications (orphans the live apps), switching the stable selector
to `matchLabels: {wave: stable}` (a new unlabelled cluster is then in no wave), or pinning prod to
an older 2.x than what runs.

Model answer: `.grading/solution/ANSWER.md`.
