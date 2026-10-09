# Workbook specification

Three workbooks share one layout and one grader. A workbook is an HTML page with the
problems and a self-exam quiz; each hands-on problem is a folder you solve in your editor
and grade with `/grade <track>/<id>` in Claude Code, run from this directory.

```
workbooks/
  SPEC.md                     this file
  README.md                   how to use the workbooks
  .claude/skills/grade/       the /grade skill
  tools/update_grades.py      records attempts, regenerates grades/grades.js
  tools/doctor.sh             toolchain check
  grades/grades.json          source of truth for scores
  grades/grades.js            generated: window.GRADES = {...}; loaded by every workbook
  grades/feedback/<track>/<id>/<timestamp>.md
  <track>/workbook.html       track = fde | go | ms
  <track>/exercises/<id>/     one folder per hands-on exercise
```

## Exercise ids

`w<week>-c<n>` for coding, `w<week>-t<n>` for troubleshooting, `ai-c<n>` / `ai-t<n>` for the
AI Integration page, `x-<n>` for add-on weeks. The full id used by the grader and the HTML is
`<track>/<id>`, e.g. `fde/w1-c1`, `go/w4-t1`, `ms/w6-c1`.

## Exercise folder

```
<track>/exercises/<id>/
  README.md        scenario, task, acceptance criteria, how to run, what to submit
  Makefile         targets below (bash, portable macOS + Linux)
  ...starter files the learner edits
  ANSWER.md        template the learner fills in (always present; see below)
  .grading/
    rubric.md      criteria and points, total 100
    grade.sh       runs every automated check; prints a summary line (below)
    tests/         hidden tests (may be empty for review-only exercises)
    reference.md   reference solution and explanation; shown only on request or after a pass
    solution/      reference files overlaid on the starter to self-validate grade.sh
```

Validation (authoring requirement): `grade.sh` run against the untouched starter must work and
report failures; run against a temp copy of the exercise with `.grading/solution/` overlaid it
must report all tests passing. Troubleshooting `solution/` holds the fixed files plus a model
`ANSWER.md`.

Make targets:
- `make setup`  prepare the scenario (install deps, start containers/kind, inject the fault). Idempotent.
- `make test`   visible tests the learner may run freely.
- `make clean`  tear down anything `setup` started.

`ANSWER.md` sections, all exercises:
- `## Approach` - what you did and why (coding) or how you investigated (troubleshooting).
- `## Root cause` - troubleshooting only: the actual cause, with evidence (commands + output excerpts).
- `## Fix` - what you changed; for troubleshooting also how you verified it.
- `## Trade-offs / what I would do in production` - short.

`.grading/grade.sh` contract:
- Run from the exercise folder; never modifies learner files (copy to a temp dir if a check needs to write).
- Bounded: every external step has a timeout; total runtime target under 5 minutes. Hidden
  tests use bounded waits (no unbounded channel receives, WaitGroups or polls), so one deadlock
  in learner code fails a single test instead of hanging the package.
- Guard tests: hidden tests that already pass on the starter (regression guards against a fix
  that breaks working behavior) are allowed. Rubrics with many guards weight the tests row
  lower (about 30 points) so the score reflects the fix and the root cause.
- Last line of stdout: `GRADE_TESTS {"passed": <int>, "total": <int>}`.
- Exit 0 even when tests fail (failures are data, not errors); exit non-zero only when the harness itself is broken, with a clear message.
- No network calls to paid APIs. Anything that would call the Claude API uses a fake client or recorded fixtures; a live run may be offered as an optional `make live` target that the grader never runs.

`rubric.md` format:

```
# Rubric: <track>/<id> <title>
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 40 | points = 40 * passed / total from grade.sh |
| 2 | <criterion> | 20 | <what full, partial and zero credit look like> |
...
Total: 100
```

Every rubric has an automated-checks row where one exists. Troubleshooting rubrics weigh the
root-cause explanation and evidence, not just the fixed state. Weights reflect what a senior
interviewer would care about for that problem.

## Exercise quality bar

- Real-world shaped: a plausible production scenario with a named fictional company or system,
  realistic logs and configs, and a reason anyone would care. No toy "reverse a string" tasks.
- Coding exercises: starter code compiles/imports and has TODOs; visible tests cover the happy
  path; hidden tests cover edge cases, failure paths and the requirements stated in the README.
- Troubleshooting exercises: `make setup` produces a genuinely broken system (container,
  kind cluster, process, or a realistic artifact bundle of logs/configs/traces when a live system
  is impossible). Symptoms are described the way a user or pager would report them, not the
  cause. One primary root cause, optionally one red herring. `grade.sh` verifies the fixed state.
- Scope: 1-3 hours each. State the estimate in the README.
- Tailored to the learner: 26 years in IT, CKA/CKAD/CKS, AWS SA/DVA/SOA, ex-AWS Solutions Architect
  and Amazon Connect/Chime SDK SRE, strong Python and TypeScript, Terraform/CDK, EKS/ArgoCD/Flux,
  has already built ADF pipelines (Azure SQL to Dataverse) and ADF-driven AI workloads. Little Go.
  Do not set beginner exercises in areas they already master; go straight to senior-level depth.
- ASCII punctuation only in every file (no em-dash, en-dash, smart quotes, ellipsis char, unicode arrows).
- Shell scripts: brace every expansion `${var}`; no process substitution `<(...)`.

## workbook.html

Self-contained single file in the same visual style and behavior as `../study-plan.html`
(tabs via hash, light/dark, localStorage). Required pieces:

1. `<script src="../grades/grades.js"></script>` in the head, before the page script.
2. Tabs: Overview, one tab per study-plan week that has exercises, AI Integration (if the
   study guide has that page), Self-exam, Scoreboard.
3. Each exercise is a card with `data-ex="<track>/<id>"` showing: title, type (coding /
   troubleshooting), estimate, the scenario summary, the task, acceptance criteria, the folder
   path, the commands (`make setup`, `make test`, `/grade <track>/<id>`), and links to the
   study-guide materials it practices. A grade badge on the card reads `window.GRADES[id]`:
   not attempted / latest and best score, pass (>= 70) or retry, and a link to the latest
   feedback file. `update_grades.py` stores the path relative to the workbooks root
   (`grades/feedback/...`), so the page links `../` + that path; it opens as plain text.
4. Self-exam tab: multiple-choice and multi-select questions scored in the browser with
   explanations shown after answering, saved to localStorage under the workbook's key.
   Group by week. For the Microsoft track, write them in exam style (scenario stems, "choose two",
   case-study sets) mapped to skills-measured areas. Aim for 10-15 questions per study week.
5. Scoreboard tab: every exercise with latest/best score, pass/retry, attempts, and the quiz
   score per week; overall percent complete.
6. The page notes at the top: "Scores update after /grade; reload the page."
7. localStorage key distinct per workbook: `wb-fde-v1`, `wb-go-v1`, `wb-ms-v1`.
