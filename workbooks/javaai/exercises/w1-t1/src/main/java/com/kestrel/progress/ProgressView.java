package com.kestrel.progress;

import java.util.List;

/** The learner dashboard read model. Field names are a contract with the Angular app. */
public record ProgressView(String learnerId, List<CourseProgress> courses) {
    public record CourseProgress(String slug, String title, int lessonsTotal, int lessonsMastered,
                                 double percentComplete, List<LessonProgress> lessons) { }
    /** mastered = at least one correct attempt on the lesson's quiz. */
    public record LessonProgress(long lessonId, int position, String title, int attempts, int correct, boolean mastered) { }
}
