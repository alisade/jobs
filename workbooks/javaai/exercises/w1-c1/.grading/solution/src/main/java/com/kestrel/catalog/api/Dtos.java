package com.kestrel.catalog.api;

import com.kestrel.catalog.domain.Level;
import jakarta.validation.constraints.*;
import java.util.List;

/** Request and response contracts of the catalog API. Records keep them immutable. */
public final class Dtos {
    private Dtos() { }

    public record CreateCourse(
            @NotBlank @Size(min = 3, max = 60)
            @Pattern(regexp = "^[a-z0-9]+(-[a-z0-9]+)*$", message = "lower-case words separated by single hyphens")
            String slug,
            @NotBlank @Size(max = 200) String title,
            @NotNull Level level) { }

    public record CourseView(Long id, String slug, String title, String level, String status) { }

    public record CreateLesson(@NotBlank @Size(max = 200) String title, @NotNull @Min(1) Integer position) { }

    public record LessonView(Long id, String courseSlug, int position, String title) { }

    @ValidQuizItem
    public record CreateQuizItem(
            @NotBlank @Size(max = 1000) String stem,
            @NotNull @Size(min = 2, max = 6) List<@NotBlank @Size(max = 500) String> options,
            @NotNull @Min(0) Integer answerIndex,
            @NotBlank @Size(max = 2000) String explanation) { }

    /** What an author sees after creating an item: includes the key. */
    public record QuizItemAuthorView(Long id, Long lessonId, String stem, List<String> options,
                                     int answerIndex, String explanation) { }

    /** What a learner sees before answering: no key, no explanation. */
    public record QuizItemLearnerView(Long id, String stem, List<String> options) { }

    public record SubmitAttempt(@NotBlank @Size(max = 64) String learnerId, @NotNull @Min(0) Integer chosenIndex) { }

    public record AttemptResult(Long attemptId, boolean correct, String explanation) { }

    public record PageView<T>(List<T> items, int page, int size, long total) { }
}
