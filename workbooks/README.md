# Workbooks

Hands-on coding and troubleshooting exercises for the study guides, plus browser self-exams.

| Track | Workbook | Study guide |
|---|---|---|
| `fde` | [fde/workbook.html](fde/workbook.html) | [../study-plan.html](../study-plan.html) |
| `go` | [go/workbook.html](go/workbook.html) | [../golang-architect-study-plan.html](../golang-architect-study-plan.html) |
| `ms` | [ms/workbook.html](ms/workbook.html) | [../microsoft-adf-powerapps-study-plan.html](../microsoft-adf-powerapps-study-plan.html) |
| `connect` | [connect/workbook.html](connect/workbook.html) | [../amazon-connect-study-plan.html](../amazon-connect-study-plan.html) |
| `audit` | [audit/workbook.html](audit/workbook.html) | [../agentic-audit-study-plan.html](../agentic-audit-study-plan.html) |
| `modernize` | [modernize/workbook.html](modernize/workbook.html) | [../lead-ai-modernization-study-plan.html](../lead-ai-modernization-study-plan.html) |
| `genai` | [genai/workbook.html](genai/workbook.html) | [../genai-agentic-engineer-study-plan.html](../genai-agentic-engineer-study-plan.html) |
| `awsfde` | [awsfde/workbook.html](awsfde/workbook.html) | [../aws-fde-agentic-study-plan.html](../aws-fde-agentic-study-plan.html) |
| `javaai` | [javaai/workbook.html](javaai/workbook.html) | [../java-fullstack-ai-study-plan.html](../java-fullstack-ai-study-plan.html) |
| `platform` | [platform/workbook.html](platform/workbook.html) | [../gcp-platform-engineer-study-plan.html](../gcp-platform-engineer-study-plan.html) |
| `backend` | [backend/workbook.html](backend/workbook.html) | [../ai-backend-data-platform-study-plan.html](../ai-backend-data-platform-study-plan.html) |
| `edgefde` | [edgefde/workbook.html](edgefde/workbook.html) | [../fde-edge-ai-study-plan.html](../fde-edge-ai-study-plan.html) |
| `aiarch` | [aiarch/workbook.html](aiarch/workbook.html) | [../aws-ai-architect-agentcore-study-plan.html](../aws-ai-architect-agentcore-study-plan.html) |
| `healthai` | [healthai/workbook.html](healthai/workbook.html) | [../lead-ai-ml-gcp-healthcare-study-plan.html](../lead-ai-ml-gcp-healthcare-study-plan.html) |

## Workflow

1. Check your tools once per track: `tools/doctor.sh fde` (or any track name in the table above).
   The newer tracks then need `make deps` once in the track folder to build its
   shared `.venv` / `node_modules`.
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
- The workbooks live in the `jobs` repo. Commit after each exercise if you want history;
  `git checkout -- <track>/exercises/<id>` (run from this directory) resets an exercise to its starter state.

See [SPEC.md](SPEC.md) for the exercise format.
