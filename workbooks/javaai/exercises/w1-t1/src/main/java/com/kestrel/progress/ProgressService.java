package com.kestrel.progress;

import java.util.ArrayList;
import java.util.List;
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

    @Transactional(readOnly = true)
    public ProgressView progress(String learnerId) {
        List<ProgressView.CourseProgress> out = new ArrayList<>();
        for (Enrollment e : enrollments.findByLearnerIdOrderByEnrolledAtAscIdAsc(learnerId)) {
            Course course = e.getCourse();
            List<ProgressView.LessonProgress> lessons = new ArrayList<>();
            int mastered = 0;
            for (Lesson lesson : course.getLessons()) {
                List<QuizAttempt> tries = attempts.findByLearnerIdAndLessonId(learnerId, lesson.getId());
                int correct = (int) tries.stream().filter(QuizAttempt::isCorrect).count();
                boolean isMastered = correct > 0;
                if (isMastered) mastered++;
                lessons.add(new ProgressView.LessonProgress(lesson.getId(), lesson.getPosition(), lesson.getTitle(),
                        tries.size(), correct, isMastered));
            }
            int total = lessons.size();
            double pct = total == 0 ? 0.0 : Math.round(1000.0 * mastered / total) / 10.0;
            out.add(new ProgressView.CourseProgress(course.getSlug(), course.getTitle(), total, mastered, pct, lessons));
        }
        return new ProgressView(learnerId, out);
    }
}
