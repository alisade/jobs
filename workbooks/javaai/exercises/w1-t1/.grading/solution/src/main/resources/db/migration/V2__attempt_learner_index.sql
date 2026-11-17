-- Serves the per-learner attempt tally (where learner_id = ? group by lesson_id).
-- On PostgreSQL: CREATE INDEX CONCURRENTLY in a non-transactional migration.
CREATE INDEX ix_attempt_learner_lesson ON quiz_attempt (learner_id, lesson_id, correct);
