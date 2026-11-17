package com.kestrel.progress;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

interface CourseRepository extends JpaRepository<Course, Long> { }

interface LessonRepository extends JpaRepository<Lesson, Long> { }

/** Per-lesson tally for one learner, computed by the database. */
record LessonTally(Long lessonId, long attempts, long correct) { }

interface EnrollmentRepository extends JpaRepository<Enrollment, Long> {
    List<Enrollment> findByLearnerIdOrderByEnrolledAtAscIdAsc(String learnerId);

    /** One statement: enrollments with their course and its lessons. */
    @Query("""
            select distinct e from Enrollment e
              join fetch e.course c
              left join fetch c.lessons
             where e.learnerId = :learnerId
             order by e.enrolledAt, e.id
            """)
    List<Enrollment> findWithCourseAndLessons(@Param("learnerId") String learnerId);
}

interface QuizAttemptRepository extends JpaRepository<QuizAttempt, Long> {
    List<QuizAttempt> findByLearnerIdAndLessonId(String learnerId, Long lessonId);

    /** One statement: attempts and correct answers per lesson for the learner. */
    @Query("""
            select new com.kestrel.progress.LessonTally(a.lesson.id, count(a),
                   sum(case when a.correct = true then 1 else 0 end))
              from QuizAttempt a
             where a.learnerId = :learnerId
             group by a.lesson.id
            """)
    List<LessonTally> tallyByLesson(@Param("learnerId") String learnerId);
}
