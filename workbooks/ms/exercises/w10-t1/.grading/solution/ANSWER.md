# ms/w10-t1 answer (model)

## Approach
Started from the symptom (balance questions get leave-request questions) and the only change in the
window (`incident/solution-history.csv`: 1.8.0.0 on 2026-10-02 added the leave submission tool). The
activity maps show which component the planner chose; analytics show how often; then I read the tool
definitions the planner sees.

## Root cause
The new Submit tool was cloned from the balance tool and its name and description were never rewritten.
Generative orchestration picks tools mainly by description, so two tools with the same description are a
coin toss that the input descriptions then tip:

- `agent/tools/SubmitLeaveRequest.tool.yaml`: `modelDisplayName: Leave and PTO`,
  `modelDescription: Handles leave and PTO for employees.`
- `agent/tools/GetPtoBalance.tool.yaml`: `modelDescription: Handles leave and PTO for employees.`
  (identical), and its only input `employeeId` has no description.
- The Submit tool's input descriptions talk about "vacation days ... the employee is asking about" and
  "how many hours or days of leave are left", i.e. balance language, so it wins every balance question.

Evidence:
- `incident/activity-map/conv-7f3a1c.json`: "how many vacation days do I have left?" -> plan step 1
  `tool:SubmitLeaveRequest` ("Leave and PTO"), generated questions "What is the first day of your leave?",
  outcome abandoned. Same for conv-7f3b02, conv-7f3e4b, conv-7f3f80.
- `incident/analytics/tool-usage-2026-W41.csv`: "Leave and PTO" 1874 invocations, 1502 abandoned after
  the first question; "Get PTO balance" only 37.
- `incident/analytics/session-outcomes-2026-W40-W41.csv`: abandoned 312 -> 1354, CSAT 4.1 -> 2.6.
- `incident/evaluation/test-set-run-2026-10-06.csv`: the balance cases FAIL, routed to the Submit tool.
  The test set was run the day AFTER the import, so it did not gate the release.

Not the cause: `incident/knowledge/indexing-status.log` warns that 3 large files on the Facilities site were
skipped. That source is about buildings and parking, it is never chosen for leave questions, and the
warning predates the incident (it appears every night of the week).

## Fix
- Renamed the tools ("Get time off balance", "Submit time off request") and wrote distinct descriptions:
  what each does, when to use it, and what it does not do (Learn's guidance for similar tools).
- Gave `employeeId` a description that says to fill it from the signed-in user's profile.
- Rewrote the Submit inputs to describe dates and hours to book, removing balance wording.
- Verified: `make test` and the full regression set route correctly; I would repeat the incident
  utterances in the Copilot Studio test pane and read the activity map before importing.

## Trade-offs / what I would do in production
- Make the evaluation test set (balance, submit, policy, holiday, paraphrases) a release gate in the
  pipeline, run on the target before the import is approved, not after.
- Review tool names/descriptions like code: a cloned component must change name and description.
- Keep a human confirmation step before the Submit tool writes to Workday (agent instructions plus the
  tool's own confirmation), so a misroute can never book leave.
- Alert on analytics: tool abandonment rate and session outcomes per release.
