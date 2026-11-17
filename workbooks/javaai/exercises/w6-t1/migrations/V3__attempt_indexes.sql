-- PERF-88: speed up the nightly export (WHERE created_at >= ? ORDER BY created_at)
CREATE INDEX idx_attempt_created_learner ON quiz_attempt (created_at, learner_id);
