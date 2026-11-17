package com.kestrel.catalog.domain;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CourseRepository extends JpaRepository<Course, Long> {
    Optional<Course> findBySlug(String slug);
    Page<Course> findByStatus(CourseStatus status, Pageable pageable);
}
