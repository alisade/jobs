package com.kestrel.catalog.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "quiz_attempt")
public class QuizAttempt {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "quiz_item_id", nullable = false)
    private QuizItem quizItem;

    @Column(name = "learner_id", nullable = false, length = 64)
    private String learnerId;

    @Column(name = "chosen_index", nullable = false)
    private int chosenIndex;

    @Column(nullable = false)
    private boolean correct;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt = OffsetDateTime.now();

    protected QuizAttempt() { }

    public QuizAttempt(QuizItem quizItem, String learnerId, int chosenIndex, boolean correct) {
        this.quizItem = quizItem;
        this.learnerId = learnerId;
        this.chosenIndex = chosenIndex;
        this.correct = correct;
    }

    public Long getId() { return id; }
    public QuizItem getQuizItem() { return quizItem; }
    public String getLearnerId() { return learnerId; }
    public int getChosenIndex() { return chosenIndex; }
    public boolean isCorrect() { return correct; }
}
