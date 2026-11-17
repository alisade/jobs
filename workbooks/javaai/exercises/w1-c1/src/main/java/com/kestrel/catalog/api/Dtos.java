package com.kestrel.catalog.api;

import com.kestrel.catalog.domain.Level;
import java.util.List;

/**
 * Request and response contracts of the catalog API. Records keep them immutable.
 *
 * TODO(w1-c1): add Bean Validation so that bad input is a 400 problem detail, not a 500 or a
 * row in the database. See README "Requirements" for every rule.
 */
public final class Dtos {
    private Dtos() { }

    public record CreateCourse(String slug, String title, Level level) { }

    public record CourseView(Long id, String slug, String title, String level, String status) { }

    public record CreateLesson(String title, Integer position) { }

    public record LessonView(Long id, String courseSlug, int position, String title) { }

    public record CreateQuizItem(String stem, List<String> options, Integer answerIndex, String explanation) { }

    /** What an author sees after creating an item: includes the key. */
    public record QuizItemAuthorView(Long id, Long lessonId, String stem, List<String> options,
                                     int answerIndex, String explanation) { }

    /** What a learner sees.  TODO(w1-c1): must never carry the answer or the explanation. */
    public record QuizItemLearnerView(Long id, String stem, List<String> options, int answerIndex,
                                      String explanation) { }

    public record SubmitAttempt(String learnerId, Integer chosenIndex) { }

    public record AttemptResult(Long attemptId, boolean correct, String explanation) { }

    public record PageView<T>(List<T> items, int page, int size, long total) { }
}
