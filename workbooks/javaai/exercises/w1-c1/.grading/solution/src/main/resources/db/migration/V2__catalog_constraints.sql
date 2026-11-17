-- V2: the rules V1 left to the application. Additive only, safe to run against live data once
-- duplicates (if any) are cleaned up; on PostgreSQL create the index CONCURRENTLY in its own migration.
ALTER TABLE course ADD CONSTRAINT uq_course_slug UNIQUE (slug);
ALTER TABLE course ADD CONSTRAINT ck_course_level CHECK (level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED'));
ALTER TABLE course ADD CONSTRAINT ck_course_status CHECK (status IN ('DRAFT', 'PUBLISHED', 'RETIRED'));

ALTER TABLE lesson ADD CONSTRAINT fk_lesson_course FOREIGN KEY (course_id) REFERENCES course (id);
ALTER TABLE lesson ADD CONSTRAINT uq_lesson_course_position UNIQUE (course_id, position);
ALTER TABLE lesson ADD CONSTRAINT ck_lesson_position CHECK (position >= 1);

ALTER TABLE quiz_item ADD CONSTRAINT fk_quiz_item_lesson FOREIGN KEY (lesson_id) REFERENCES lesson (id);
ALTER TABLE quiz_item ADD CONSTRAINT ck_quiz_item_answer CHECK (answer_index >= 0);
CREATE INDEX ix_quiz_item_lesson ON quiz_item (lesson_id);

ALTER TABLE quiz_item_option ADD CONSTRAINT fk_option_item FOREIGN KEY (quiz_item_id) REFERENCES quiz_item (id);

ALTER TABLE quiz_attempt ADD CONSTRAINT fk_attempt_item FOREIGN KEY (quiz_item_id) REFERENCES quiz_item (id);
ALTER TABLE quiz_attempt ADD CONSTRAINT ck_attempt_chosen CHECK (chosen_index >= 0);
CREATE INDEX ix_attempt_learner_item ON quiz_attempt (learner_id, quiz_item_id, created_at);
