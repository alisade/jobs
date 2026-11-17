CREATE TABLE quiz_attempt (
    id INTEGER PRIMARY KEY,
    learner_id TEXT NOT NULL REFERENCES learner(id),
    quiz_item_id INTEGER NOT NULL REFERENCES quiz_item(id),
    course_id TEXT NOT NULL REFERENCES course(id),
    chosen_index INTEGER NOT NULL,
    correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
    created_at TEXT NOT NULL  -- ISO 8601 UTC, e.g. 2026-10-14T08:15:32Z
);
