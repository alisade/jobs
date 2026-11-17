# Rubric: healthai/w1-t1 The CMS clock report says zero late decisions
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause and evidence | 35 | Full: `add_days` defaults to business days and `decision_deadline` calls it without `business=False`, so the standard clock is 7 business days (9-11 calendar days); at least two traced cases (received, wrong due, right due, decided); counts before (0) and after (21 standard, 7 expedited unchanged); all 5 audit cases confirmed. Partial: right cause, no traced cases or numbers. Zero: blames DST or time zones. |
| 3 | Red herring handled | 10 | Shows the DST warnings are informational: the code keeps the wall-clock time on purpose and the expedited clock is elapsed hours; gives a case that crosses Nov 1 and is computed correctly. |
| 4 | Prevention and impact | 20 | Names the operational impact (the reviewer queue showed too much time remaining, so real cases may have been decided late), proposes table-driven tests from the rule text, removing the dangerous default (`business` keyword-only and no default, or separate functions), compliance sign-off on rule interpretation, and an independent recompute check before publishing. |
Total: 100
