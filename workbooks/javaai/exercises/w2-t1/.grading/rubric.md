# Rubric: javaai/w2-t1 The quiz shows the previous lesson's questions and answers are rejected
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: QuizPageStore flattens selections with mergeMap, so every request stays alive and whichever response arrives last wins; select() sets lessonId immediately but the slow lesson-2 response overwrites quiz afterwards, so state pairs lessonId 3 with lesson-2 items and keeps the old answers; submit posts lesson 3 with item ids 201-203 and the backend correctly returns 409. Introduced in app 1.6 with the reactive store; needs a slow network to reorder responses. Partial (10-15): "race condition" without the operator and the state mismatch. Zero: cache. |
| 3 | Evidence | 20 | HAR: request 1 (lesson 2) sent before 2 but ending 2.6 s later; the 409 body naming item 201 for lesson 3; error beacons concentrated on 3g/2g; reports starting with release 1.6; a failing test that releases responses out of order. |
| 4 | Red herring handled | 10 | Both quiz requests were cache misses; max-age=300 existed since 0.2 without reports; the URL is per lesson so a cached response is the right lesson's quiz; no-store would cost CDN hits and fix nothing. |
| 5 | Fix quality | 10 | switchMap (cancels in-flight HTTP), clear quiz and answers on select, gate submit on loading and lessonId match, ignore foreign answers, error state reset on the next select. |
| 6 | Production follow-ups | 5 | Marble or out-of-order tests for every flattening operator in the app, a throttled-network e2e, lint rule or review checklist for mergeMap on user-driven streams, keep the server-side 409 as the backstop. |
Total: 100
