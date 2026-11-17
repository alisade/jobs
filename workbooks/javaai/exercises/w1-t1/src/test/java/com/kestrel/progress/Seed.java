package com.kestrel.progress;

import org.springframework.jdbc.core.JdbcTemplate;

/** Test data: a learner enrolled in N courses of M lessons with a deterministic attempt pattern. */
public final class Seed {
    private Seed() { }

    /** Lesson k (1-based) of each course gets k % 3 attempts; the last attempt is correct when k is even. */
    public static void learner(JdbcTemplate jdbc, String learnerId, String prefix, int courses, int lessons) {
        for (int c = 1; c <= courses; c++) {
            String slug = prefix + "-course-" + c;
            jdbc.update("insert into course(slug, title) values (?, ?)", slug, "Course " + c + " (" + prefix + ")");
            Long courseId = jdbc.queryForObject("select id from course where slug = ?", Long.class, slug);
            jdbc.update("insert into enrollment(learner_id, course_id, enrolled_at) values (?, ?, ?)",
                    learnerId, courseId, java.time.OffsetDateTime.parse("2026-09-01T00:00:00Z").plusDays(c));
            // insert lessons in reverse to prove ordering comes from position, not insertion order
            for (int l = lessons; l >= 1; l--) {
                jdbc.update("insert into lesson(course_id, position, title) values (?, ?, ?)", courseId, l, "Lesson " + l);
            }
            for (int l = 1; l <= lessons; l++) {
                Long lessonId = jdbc.queryForObject("select id from lesson where course_id = ? and position = ?", Long.class, courseId, l);
                int n = l % 3;
                for (int a = 1; a <= n; a++) {
                    boolean correct = a == n && l % 2 == 0;
                    jdbc.update("insert into quiz_attempt(learner_id, lesson_id, correct, created_at) values (?, ?, ?, current_timestamp)",
                            learnerId, lessonId, correct);
                }
                // noise: another learner's attempts on the same lesson must not count
                jdbc.update("insert into quiz_attempt(learner_id, lesson_id, correct, created_at) values (?, ?, true, current_timestamp)",
                        "other-" + learnerId, lessonId);
            }
        }
    }
}
