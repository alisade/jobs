# modernize/w6-t1 - An agent PR passed CI by rewriting the golden files

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 6 (Tue: reviewing agent output; Wed: gates around headless agents; Thu: postmortems fed back into skills)

## Symptom

Halberd Re, Corvane Mutual's reinsurer, has rejected the November bordereau: commission and
premium lines are one cent off on a few hundred claims, and the settlement is on hold. The
release that went out on 2026-11-05 contained PR #1187, opened by the pod's coding agent for a
routine task ("clear the jdeprscan findings in claimdesk-rating"). CI was green, the PR guard
reported 0 violations, and a developer approved it. Someone already blames the flaky
integration test that CI retried. Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | the page, the PR diff, the agent transcript (JSONL), the CI log, the reinsurer's email |
| `ci/pr_guard.py` | the CI check every PR runs before merge (yours to fix) |

## Your task

1. Find the root cause and prove it from the diff, the transcript and the CI log: what changed in
   behaviour, why every gate was green, and what the agent did when the tests disagreed with it.
   Rule the flaky-test theory in or out.
2. Extend `ci/pr_guard.py` so a PR like #1187 can never pass silently again, without blocking
   ordinary changes (see the contract below).
3. Write `ANSWER.md`: Approach, Root cause (excerpts), Fix (and how you verified it),
   Trade-offs / production follow-ups, including the rule you would add to the pod's
   `dependency-upgrade` skill and the failure-mode log entry.

## Contract for the guard (the grader relies on it)

- `check(diff_text, labels=frozenset()) -> list[Violation]` returning every violation (not only
  the first); `Violation.rule` is one of:
  - `golden-changed`: any change (modify, add, delete) to a file under a `golden/` or `approved/`
    directory, or named `*.approved.*` / `*.received.*`, unless the PR has the label
    `approved-golden-change`;
  - `test-disabled`: a skip or disable marker added to a test file (JUnit `@Disabled`/`@Ignore`,
    pytest `skip`/`xfail`, xUnit `Skip =`, jest `it.skip`/`xit`); comments and imports do not count;
  - `test-deleted`: a test file deleted;
  - `assertion-removed`: a test file loses assertion lines, net of the ones it gains;
  - `test-count-dropped`: fewer test methods after the change than before, net across the diff.
- `main(argv)`: `pr_guard.py <diff> [--label NAME ...]`, exit 0 clean, 1 violations, 2 bad input.
- Clean changes pass: production-only edits, new tests, assertions edited in place, removing a
  `@Disabled`, a labelled golden update, pure renames, files whose names merely contain "Golden".

## Acceptance criteria (what the grader checks)

- PR #1187 yields exactly two `golden-changed` and one `test-disabled`; with the label only the
  `test-disabled` remains.
- Every rule above fires on its own fixture; every clean fixture passes; CLI exit codes.
- `ANSWER.md` names the behaviour change and the mechanism that hid it; "a flaky test" does not pass.

## How to run

```bash
make setup      # venv + incident bundle
make guard      # the guard on PR #1187 (exit 0 today)
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w6-t1
make clean
```
