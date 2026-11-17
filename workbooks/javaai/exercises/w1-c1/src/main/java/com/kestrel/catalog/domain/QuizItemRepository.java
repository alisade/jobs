package com.kestrel.catalog.domain;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QuizItemRepository extends JpaRepository<QuizItem, Long> {
    List<QuizItem> findByLessonIdOrderById(Long lessonId);
}
