CREATE TABLE enrollment (learner_id TEXT NOT NULL REFERENCES learner(id), course_id TEXT NOT NULL REFERENCES course(id),
    enrolled_at TEXT NOT NULL, PRIMARY KEY (learner_id, course_id));
