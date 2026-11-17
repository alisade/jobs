# javaai/w3-t1 - "Generate quiz" fails for biology, history and psychology lessons

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 3 (Wed: safety filters and blocked responses; Tue: quotas and 429s)

## Symptom

Course Ops reports that since Monday, "Generate quiz" shows "Something went wrong" for many
biology, history and psychology lessons; statistics and CS lessons are fine and retrying does not
help. The Cloud Run error rate of `quiz-gen` (Python FastAPI, Gemini on Vertex AI) went from 2.3%
on Sunday to 17.8% on Monday. L2 sees 429 RESOURCE_EXHAUSTED in the logs on both days and wants a
quota increase and 6 retries instead of 3. Release 2.3 went out Monday 07:10 UTC. Start with
`incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt`, `metrics.txt` | the report, work notes, Cloud Monitoring numbers |
| `incident/quizgen-logs-2026-11-09_10.log` | Cloud Logging export for Sunday and Monday |
| `incident/release-2.3.diff` | what changed in release 2.3 |
| `quizsvc/service.py`, `quizsvc/app.py` | the service |
| `quizsvc/gemini.py` | replay stand-in for Gemini (plays the managed service: do not edit) |
| `config/safety.yaml` | safety thresholds sent with every request |
| `fixtures/` | pilot lessons and recorded responses with their safety ratings |

## Your task

1. Find the root cause and prove it with the logs, the diff and a local reproduction
   (`make run`, or call `service.generate_quiz` for a failing lesson and print the raw response).
2. Explain the Sunday errors too: they were there before the release.
3. Rule the quota theory in or out with evidence.
4. Fix it: ordinary university course content generates again; content that is still blocked
   returns HTTP 422 with `status: "blocked"`, `source` (`prompt` or `response`), `category` and a
   human-readable `message` (never a 500, never a stack trace); keep a threshold for every category.
5. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups).

## Acceptance criteria (what the grader checks)

- No pilot lesson produces a 500; the six ordinary lessons return 200 with 3 items.
- The high-risk lesson returns a graceful 422 with the fields above; prompt-level blocks are handled.
- `config/safety.yaml` has all four categories at a threshold suitable for adult learners
  (not `BLOCK_LOW_AND_ABOVE`, not `BLOCK_NONE`/`OFF`).
- 429 handling still works.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup
make test
make run      # optional: POST http://localhost:8081/quiz/generate {"lessonId": "bio-210-l4"}
# from workbooks/: /grade javaai/w3-t1
make clean
```
