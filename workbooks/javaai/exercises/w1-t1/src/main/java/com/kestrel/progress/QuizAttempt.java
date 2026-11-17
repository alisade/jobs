package com.kestrel.progress;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "quiz_attempt")
public class QuizAttempt {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "learner_id", nullable = false) private String learnerId;
    @ManyToOne(fetch = FetchType.LAZY, optional = false) @JoinColumn(name = "lesson_id") private Lesson lesson;
    @Column(nullable = false) private boolean correct;
    @Column(name = "created_at", nullable = false) private OffsetDateTime createdAt = OffsetDateTime.now();

    protected QuizAttempt() { }
    public QuizAttempt(String learnerId, Lesson lesson, boolean correct) { this.learnerId = learnerId; this.lesson = lesson; this.correct = correct; }

    public Long getId() { return id; }
    public String getLearnerId() { return learnerId; }
    public Lesson getLesson() { return lesson; }
    public boolean isCorrect() { return correct; }
}
