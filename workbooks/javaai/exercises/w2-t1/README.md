# javaai/w2-t1 - The quiz shows the previous lesson's questions and answers are rejected

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 2 (Tue: signals and RxJS flattening operators; Wed: HttpClient)

## Symptom

Learners report that after clicking a new lesson the quiz still shows the previous lesson's
questions, and submitting fails with "your answers were not saved". It mostly happens on slow
connections and goes away if they click the lesson again. The backend returns 409 "quiz item does
not belong to lesson". L2 suspects the CDN cache (`Cache-Control: max-age=300`) and wants
`no-store`. Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/` | the page, a HAR summary from one learner, client error beacons, CDN headers |
| `src/quizPageStore.ts` | the store behind the quiz screen (Angular component reads it with `toSignal`) |
| `src/quizApi.ts` | the API contract |
| `tests/fakeApi.ts` | a fake API whose responses you release in any order |

## Your task

1. Find the root cause and prove it: reproduce it in a test with responses arriving out of order.
2. Rule the cache theory in or out with evidence from the bundle.
3. Fix the store: the latest selected lesson always wins, the previous request is cancelled, the
   old quiz and answers are cleared while the new one loads (no submit while loading), answers
   for items not in the current quiz are ignored, and a submit never mixes one lesson's id with
   another lesson's items. Load errors are shown and the next selection still works.
4. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups).

## Acceptance criteria (what the grader checks)

- Hidden jest tests: out-of-order responses, cancellation, clearing and submit gating, consistent
  submits, ignored foreign answers, error recovery, a same-lesson reselect guard.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup
make test
# from workbooks/: /grade javaai/w2-t1
make clean
```
