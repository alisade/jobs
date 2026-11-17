package com.kestrel.progress;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "enrollment")
public class Enrollment {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "learner_id", nullable = false) private String learnerId;
    @ManyToOne(fetch = FetchType.LAZY, optional = false) @JoinColumn(name = "course_id") private Course course;
    @Column(name = "enrolled_at", nullable = false) private OffsetDateTime enrolledAt = OffsetDateTime.now();

    protected Enrollment() { }
    public Enrollment(String learnerId, Course course) { this.learnerId = learnerId; this.course = course; }

    public Long getId() { return id; }
    public String getLearnerId() { return learnerId; }
    public Course getCourse() { return course; }
    public OffsetDateTime getEnrolledAt() { return enrolledAt; }
}
