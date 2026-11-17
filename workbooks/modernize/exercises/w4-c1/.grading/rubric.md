# Rubric: modernize/w4-c1 javax.servlet to jakarta.servlet
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh (the 8 visible characterization tests are green on the starter too; the hidden tests decide) |
| 2 | Namespace judgement | 20 | Full: jakarta.servlet for the Servlet API; javax.sql and javax.naming kept because they are Java SE; the error attributes read through `RequestDispatcher.ERROR_*` constants (the literal "javax.servlet.error.status_code" is null on Servlet 5+), explained. Partial: correct code with no explanation. Zero: golden files edited or tests weakened. |
| 3 | Use of the safety net | 15 | Full: tests run before the change (green), after the import change (red on the error flows), after the fix (green); says which flows caught what. Partial: tests only run at the end. |
| 4 | EAP 8 follow-ups | 15 | Full: web.xml / jboss-web.xml schema versions, PicketBox to Elytron, libraries still on javax (Eclipse Transformer or upgrades), OpenRewrite recipe coverage and its limits (string literals, reflection, config), rollout with the golden flows as a smoke test and the javax build as rollback. Partial: a list without reasons. |
Total: 100
