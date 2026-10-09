# Workbooks

Hands-on coding and troubleshooting exercises for the three study guides, plus browser self-exams.

| Track | Workbook | Study guide |
|---|---|---|
| `fde` | [fde/workbook.html](fde/workbook.html) | [../study-plan.html](../study-plan.html) |
| `go` | [go/workbook.html](go/workbook.html) | [../golang-architect-study-plan.html](../golang-architect-study-plan.html) |
| `ms` | [ms/workbook.html](ms/workbook.html) | [../microsoft-adf-powerapps-study-plan.html](../microsoft-adf-powerapps-study-plan.html) |

## Workflow

1. Check your tools once per track: `tools/doctor.sh fde` (or `go`, `ms`).
2. Open the workbook HTML, pick an exercise, read its card.
3. `cd <track>/exercises/<id> && make setup`, solve it in your editor, run `make test`, fill in `ANSWER.md`.
4. From this directory, start Claude Code and run `/grade <track>/<id>` (e.g. `/grade fde/w1-c1`).
   It runs the visible and hidden checks, reviews your code and `ANSWER.md` against the rubric,
   writes feedback to `grades/feedback/`, and records the score.
5. Reload the workbook page: the card and the Scoreboard show your score and link the feedback.
6. `make clean` when done. Retry as often as you like; every attempt is kept.

Other grader commands: `/grade status`, `/grade <track>/<id> --reveal` (shows the reference
solution after grading).

## Rules of the game

- Don't read `.grading/` before you submit; that is where the hidden tests and reference live.
- Pass mark is 70/100. Troubleshooting is graded mostly on the root cause and evidence in
  `ANSWER.md`, not just on the system working again.
- This is a local git repo (no remote). Commit after each exercise if you want history;
  `git checkout -- <track>/exercises/<id>` resets an exercise to its starter state.

See [SPEC.md](SPEC.md) for the exercise format.
