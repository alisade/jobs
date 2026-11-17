package com.kestrel.progress;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

interface CourseRepository extends JpaRepository<Course, Long> { }

interface LessonRepository extends JpaRepository<Lesson, Long> { }

interface EnrollmentRepository extends JpaRepository<Enrollment, Long> {
    List<Enrollment> findByLearnerIdOrderByEnrolledAtAscIdAsc(String learnerId);
}

interface QuizAttemptRepository extends JpaRepository<QuizAttempt, Long> {
    List<QuizAttempt> findByLearnerIdAndLessonId(String learnerId, Long lessonId);
}
