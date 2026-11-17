-- INC-20590: the dashboard filters by learner and course, then a created_at range, newest first.
-- Equality columns first, the range column last, so one index serves WHERE and ORDER BY.
-- (PostgreSQL: CREATE INDEX CONCURRENTLY in its own non-transactional migration.)
CREATE INDEX idx_attempt_learner_course_created ON quiz_attempt (learner_id, course_id, created_at);
