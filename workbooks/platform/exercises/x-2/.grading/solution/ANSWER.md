# ANSWER: platform/x-2 Chart 3.0 reached every cluster at once

## Approach

Read the page, then the live source of prod-blue in `evidence/argocd-app-history.txt`, then the
controller events and the ApplicationSet git log. Reproduced with `make sim`: prod-blue and
prod-green resolve `>=2.0.0` to 3.0.0 against today's index.

## Root cause

The stable ApplicationSet `riq-api-stable` has `targetRevision: '>=2.0.0'` (commit 5aa81c3,
2026-08-14, "follow latest 2.x automatically, no more bump PRs"). `>=2.0.0` is an unbounded semver
range: it means "the highest release at or above 2.0.0", not "latest 2.x". While 2.4.1 was the
highest release it behaved like the intended pin, so nobody noticed.

Chain of events:
- 14:40 Dana's commit c41e09a pinned canary to `3.0.0`; the canary apps showed
  `ComparisonError: chart riq-api version 3.0.0 not found` because 3.0.0 was not published yet.
- 15:02:44 chart-releaser published riq-api-3.0.0.tgz (index.yaml `created: 2026-11-10T15:02:41Z`).
  3.0.0-rc.1 had been in the index since 11-06 but pre-releases do not satisfy `>=2.0.0`, which is why
  nothing happened earlier.
- 15:05:59 / 15:06:02 periodic refresh of prod-blue-riq-api and prod-green-riq-api:
  `Updated sync status: Synced -> OutOfSync (resolved targetRevision '>=2.0.0' to 3.0.0)`, then
  `Initiated automated sync to '3.0.0'`. App history shows revision 42 = 3.0.0 at 15:06:02.
- values-prod.yaml still had `db.url` (the release notes say prod values change in the stable bump
  PR), so riq-api crashed with `required key database.dsn not set` on both clusters at once.

Red herring: selfHeal (9b20d7f, 11-03). selfHeal only reverts live-state drift from the desired
state; it does not choose versions. The trigger was automated sync acting on a desired state that
changed by itself when the chart index changed. With automated sync off, prod would have gone
OutOfSync and waited, so automated sync widened the blast radius, but the defect is the range.

## Fix

- `riq-api-stable`: `targetRevision: 2.4.1` (exact pin; bump by PR after the canary soak). A bounded
  range such as `~2.4` or `>=2.4.0 <3.0.0` would also be acceptable if automatic patches are wanted.
- Canary stays `3.0.0`. Selectors unchanged: canary `wave In canary`-style matchLabels, stable
  `wave NotIn [canary]`, so a new cluster without a `wave` label lands in stable exactly once.
- Verified with `make sim` today (prod 2.4.1, canary 3.0.0) and against an index with 3.1.0 and 2.5.0
  (prod still 2.4.1).

## Trade-offs / what I would do in production

- Exact pins plus bump PRs (a bot can open them) keep promotion reviewable; ranges only within a
  minor, never open-ended. Add a CI check that rejects unbounded `>=` / `*` targetRevisions on
  stable/prod ApplicationSets.
- Promotion as data: a per-wave version value (cluster label or a generator file) and one
  ApplicationSet, or ApplicationSet progressive sync (RollingSync) by wave, so a version moves
  canary -> stg -> prod-blue -> prod-green with health gates.
- Breaking chart releases: the chart should fail render on old keys (or support both) so a mismatch
  fails sync instead of crashing pods; prod values ship in the same PR as the bump.
- Automated sync can go back on for prod once the pin is in; keep selfHeal. Alert on any prod app
  revision change outside a change window.
- Postmortem action items: audit other ApplicationSets for unbounded ranges.
