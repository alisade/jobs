# Reference: javaai/w1-t1

## Root cause

Release 0.9.0 rewrote `ProgressService.progress` as nested loops over lazy associations:

- 1 statement: enrollments for the learner
- per enrollment: 1 statement for the lazy `course`, 1 for the lazy `course.lessons`
- per lesson: 1 statement `findByLearnerIdAndLessonId`

For 6-9 courses of 8-15 lessons that is 64-157 statements (session metrics in the log; an empty
learner runs 1). Each attempts query is a sequential scan of 4.1M rows (no index on
`quiz_attempt.learner_id`; V1 only indexes `created_at`). At semester-start load (30 req/s) this is
~2,300 queries/s and Cloud SQL CPU saturates. Transactions then take seconds, each holds a pool
connection for the whole time, and Hikari runs out: the "Connection is not available" errors are a
symptom.

The pool proposal (10 -> 50 per instance, 4 -> 12 instances = 600 connections) exceeds Cloud SQL's
max_connections of 100 and pushes more concurrent seq scans into a CPU-bound database: harmful.

## Fix (in `.grading/solution/`)

- `EnrollmentRepository.findWithCourseAndLessons`: `join fetch e.course c left join fetch c.lessons`
  with `distinct` - one statement.
- `QuizAttemptRepository.tallyByLesson`: `select new LessonTally(lesson.id, count, sum(case ...))
  ... where learnerId = :id group by lesson.id` - one statement.
- Lessons sorted by position in memory (fetch-joined collections do not guarantee order).
- `V2__attempt_learner_index.sql`: `(learner_id, lesson_id, correct)`, covering the tally.

Total: 2 statements per request, independent of data.

## Alternatives worth naming

- `@EntityGraph` on the repository method instead of JPQL fetch join.
- A single native SQL query with a left join and group by, mapped to a DTO.
- `hibernate.default_batch_fetch_size`: cuts statements by a factor but still grows with data.
- A precomputed progress table updated on attempt (CQRS read model) if the dashboard grows.

## Catching it earlier

A test that clears Hibernate statistics and asserts the statement count for a large learner (as
the hidden test does), or datasource-proxy's query count assertions; Query Insights alert on
calls per normalized query; a load test with realistic enrollment fan-out before semester start.
