# Reference: javaai/w2-t1

## Root cause

`select$.pipe(mergeMap(id => api.getQuiz(id)))` keeps every request alive and applies responses in
arrival order. On a slow link the learner clicks lesson 3 while lesson 2 is loading; lesson 3's
response arrives first (HAR: request 2 ends at 7215 ms) and lesson 2's later (9870 ms) overwrites
`quiz`. `lessonId` was already set to 3 in `select()`, and `answers` were never cleared, so state is
"lesson 3 with lesson-2 items". Submit posts `/lessons/3/attempts` with items 201-203 and the API
correctly answers 409. Release 1.6 introduced the store; before that the route resolver loaded the
quiz before the page rendered.

## Not the cache

Both requests were CDN misses; each lesson has its own URL, so a cached response would still be the
right quiz; max-age=300 predates the reports by two months.

## Fix (`.grading/solution/src/quizPageStore.ts`)

- `switchMap` instead of `mergeMap`: the new selection unsubscribes the old request (HttpClient aborts it).
- `select()` clears `quiz`, `answers`, `error`, `result` and sets `loading`.
- `answer()` ignores items not in the current quiz; `submit()` refuses while loading or when
  `quiz.lessonId !== lessonId`.

## Operator choice

switchMap for "latest wins" reads (navigation, search-as-you-type); exhaustMap for "ignore repeats
while busy" (a submit button); concatMap for ordered writes; mergeMap only when every result matters
independently.
