# javaai/w1-c1 - Catalog API: validation, problem details and a schema that enforces its own rules

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Tue: Spring Boot REST and Bean Validation; Wed: JPA and Flyway; Thu: error handling and testing)

## Scenario

Kestrel Learning (fictional) builds an AI tutor for open university courses. The Spring Boot
catalog API is the system of record for courses, lessons, quiz items and quiz attempts; the
Python agent service and the Gemini quiz generator only ever read from it or write through it.

Release 0.3.0 went out fast. The pilot found that:

- a malformed request (blank title, slug with spaces, 1-option quiz item) is either stored or
  answered with a 500 and a stack trace;
- two authors created the same course slug a second apart and now both exist;
- the learner quiz screen receives `answerIndex` and the explanation in the JSON, so anyone with
  the browser dev tools sees the key;
- a crawler asked for `size=100000` and the list endpoint obliged;
- the database itself enforces nothing: no unique keys, no foreign keys, no checks. V1 is
  already applied in every environment.

## What you have

| Path | What it is |
|---|---|
| `src/main/java/com/kestrel/catalog/api/CatalogController.java` | all endpoints (works on the happy path) |
| `src/main/java/com/kestrel/catalog/api/Dtos.java` | request/response records |
| `src/main/java/com/kestrel/catalog/domain/` | JPA entities and Spring Data repositories |
| `src/main/resources/db/migration/V1__catalog.sql` | the applied schema; do not edit it |
| `src/main/resources/application.properties` | H2 in PostgreSQL mode stands in for Cloud SQL |
| `src/test/java/.../CatalogHappyPathTest.java` | visible tests |

## Requirements

1. **Validation (Bean Validation on the request records)** - every failure is HTTP 400 with an
   `application/problem+json` body (RFC 9457) that has an `errors` array of `{field, message}`:
   - course: `slug` 3-60 chars matching `^[a-z0-9]+(-[a-z0-9]+)*$`; `title` not blank, max 200;
     `level` required (an unknown enum value is also a 400, never a 500).
   - lesson: `title` not blank; `position` required and >= 1.
   - quiz item: `stem` and `explanation` not blank; `options` 2 to 6 entries, none blank, distinct
     after trim and ignoring case (error on field `options`); `answerIndex` required and pointing at
     one of the options (error on field `answerIndex`).
   - attempt: `learnerId` not blank (max 64); `chosenIndex` required, >= 0 and less than the number of
     options (400 otherwise).
2. **Errors** - unknown course, lesson or quiz item: 404 problem detail. Duplicate course slug or
   duplicate lesson position in a course: 409 problem detail, also when two requests race (the
   database constraint is the backstop). No stack traces in responses.
3. **Learner view** - `GET /api/lessons/{id}/quiz-items` returns `id`, `stem`, `options` only.
   The explanation is returned after an attempt, never before.
4. **Paging** - `GET /api/courses` caps `size` at 50 (the response `size` shows the effective
   value); a negative `page` is a 400.
5. **Schema** - add a new Flyway migration (V2 or later); V1 must stay byte-identical. The
   database must reject: a duplicate course slug, a lesson whose course does not exist, two lessons
   at the same position in one course, a negative `answer_index`, an attempt for a quiz item that
   does not exist. Add an index that starts with `quiz_attempt.learner_id` for the progress queries.

## Acceptance criteria (what the grader checks)

- Hidden MockMvc tests for every rule above: status codes, `application/problem+json`, the
  `errors` array with the right field names, the learner view, the page-size cap.
- Hidden JdbcTemplate tests insert bad rows directly to prove the database enforces the rules.
- V1 checksum unchanged and at least one later migration applied.
- `ANSWER.md`: why the rules live in both the API and the schema, and how you would roll V2 out
  against a production table that may already contain duplicates.

## How to run

```bash
make setup     # JDK 21 check, Maven downloads once into ~/.m2 (Spring Boot 3.5, H2, Flyway)
make test      # visible tests
make run       # optional: the API on :8080
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade javaai/w1-c1
make clean
```

Spring Boot 4 (November 2025) is the current major line; this exercise pins 3.5 because the
posting and most production code bases are still on 3.x. Everything here carries over; be ready
to say what changed in 4 (Jakarta EE 11, Jackson 3, modular starters).
