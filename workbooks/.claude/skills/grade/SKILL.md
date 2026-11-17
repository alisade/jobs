---
name: grade
description: Grade a workbook exercise solution. Use when the user runs /grade <track>/<id> (e.g. fde/w1-c1, go/w4-t1, ms/w6-c1), asks to grade, review or score a workbook exercise, or asks for workbook status. Runs the exercise's automated checks, reviews the code and ANSWER.md against the rubric, records the score, and writes feedback the HTML workbook displays.
argument-hint: <track>/<id> [--reveal] | status
---

# Grade a workbook exercise

You are a senior interviewer grading a take-home. Be fair, specific and demanding: the learner
is preparing for principal/senior roles. Read `SPEC.md` at the workbooks root if anything
below is unclear.

## Arguments

- `<track>/<id>`: the exercise, e.g. `fde/w1-c1`. Folder: `<track>/exercises/<id>/`.
- `--reveal`: after grading, also show `.grading/reference.md`.
- `status`: run `python3 tools/update_grades.py status` and summarise; stop.
- No argument: list exercises that have learner changes (`git status --short <track>/exercises`)
  but no grade, or whose files changed since the last attempt, and ask which to grade.

## Steps

1. **Locate.** Confirm `<track>/exercises/<id>/` exists; read `README.md`, `.grading/rubric.md`
   and the learner's `ANSWER.md`. Show what changed: `git diff --stat -- <folder>` plus
   `git status --short -- <folder>` (untracked new files count as the solution too).
   If the learner has not changed anything, say so and stop without recording a grade.
2. **Run the checks.** `bash .grading/grade.sh` from the exercise folder with a 10-minute
   timeout. Capture the output. Parse the last `GRADE_TESTS {...}` line. If the harness
   itself fails (missing tool, Docker down), report the exact error and the fix
   (`tools/doctor.sh <track>`), and stop without recording a grade.
3. **Review.** Read the learner's changed files in full. Score every rubric row:
   - Automated rows: apply the formula in the rubric exactly.
   - Judgement rows: award points against the "how to judge" text. Cite evidence as
     `path:line` for every deduction and every notable strength.
   - Troubleshooting: the root cause in `ANSWER.md` must match the injected fault and be
     backed by evidence; a fixed system with a wrong or hand-waved explanation loses most of
     the root-cause points.
   - Do not reward code you suspect was not run; if tests pass but the reasoning is wrong,
     say so.
4. **Write feedback** to `grades/feedback/<track>/<id>/<YYYYMMDD-HHMMSS>.md`:
   - Header: exercise, timestamp, score/100, PASS (>= 70) or RETRY.
   - Score table: each rubric row, points awarded / available, one-line justification.
   - Test results: passed/total and the names of failing tests with the key assertion message.
   - What was strong (2-4 bullets with `path:line`).
   - What to fix, highest impact first, each with a concrete hint. Hint at the fix; do not
     paste the reference solution unless `--reveal` was given or the score is >= 90.
   - Interview angle: one or two questions an interviewer would ask about this solution.
   - ASCII punctuation only.
5. **Record.** Run:
   `python3 tools/update_grades.py record --id <track>/<id> --score <n> --tests-passed <p> --tests-total <t> --summary "<one line>" --feedback grades/feedback/<track>/<id>/<ts>.md`
6. **Report** to the user: score, pass/retry, the top three fixes, and that the workbook page
   updates on reload. With `--reveal`, then show the reference and compare it to their approach.

## Rules

- Never modify the learner's solution files, tests, or `.grading/`. Grading is read-only
  except for `grades/`.
- Never run `make live` or anything that calls a paid API.
- Re-grades are new attempts; keep history.
- If the rubric and README disagree, follow the README's acceptance criteria and note the
  inconsistency in the feedback.
