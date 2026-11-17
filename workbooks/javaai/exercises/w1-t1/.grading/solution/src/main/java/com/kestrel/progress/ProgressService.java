package com.kestrel.progress;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProgressService {

    private final EnrollmentRepository enrollments;
    private final QuizAttemptRepository attempts;

    public ProgressService(EnrollmentRepository enrollments, QuizAttemptRepository attempts) {
        this.enrollments = enrollments;
        this.attempts = attempts;
    }

    /** Two statements regardless of how many courses, lessons or attempts the learner has. */
    @Transactional(readOnly = true)
    public ProgressView progress(String learnerId) {
        List<Enrollment> list = enrollments.findWithCourseAndLessons(learnerId);
        if (list.isEmpty()) return new ProgressView(learnerId, List.of());
        Map<Long, LessonTally> tally = attempts.tallyByLesson(learnerId).stream()
                .collect(Collectors.toMap(LessonTally::lessonId, Function.identity()));

        List<ProgressView.CourseProgress> out = new ArrayList<>();
        for (Enrollment e : list) {
            Course course = e.getCourse();
            List<ProgressView.LessonProgress> lessons = new ArrayList<>();
            int mastered = 0;
            List<Lesson> ordered = course.getLessons().stream()
                    .sorted(Comparator.comparingInt(Lesson::getPosition)).toList();
            for (Lesson lesson : ordered) {
                LessonTally t = tally.get(lesson.getId());
                int tries = t == null ? 0 : (int) t.attempts();
                int correct = t == null ? 0 : (int) t.correct();
                boolean isMastered = correct > 0;
                if (isMastered) mastered++;
                lessons.add(new ProgressView.LessonProgress(lesson.getId(), lesson.getPosition(), lesson.getTitle(),
                        tries, correct, isMastered));
            }
            int total = lessons.size();
            double pct = total == 0 ? 0.0 : Math.round(1000.0 * mastered / total) / 10.0;
            out.add(new ProgressView.CourseProgress(course.getSlug(), course.getTitle(), total, mastered, pct, lessons));
        }
        return new ProgressView(learnerId, out);
    }
}
