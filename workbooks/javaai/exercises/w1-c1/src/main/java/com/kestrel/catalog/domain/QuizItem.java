package com.kestrel.catalog.domain;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "quiz_item")
public class QuizItem {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "lesson_id", nullable = false)
    private Lesson lesson;

    @Column(nullable = false, length = 1000)
    private String stem;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "quiz_item_option", joinColumns = @JoinColumn(name = "quiz_item_id"))
    @OrderColumn(name = "option_order")
    @Column(name = "option_text", nullable = false, length = 500)
    private List<String> options = new ArrayList<>();

    @Column(name = "answer_index", nullable = false)
    private int answerIndex;

    @Column(nullable = false, length = 2000)
    private String explanation;

    protected QuizItem() { }

    public QuizItem(Lesson lesson, String stem, List<String> options, int answerIndex, String explanation) {
        this.lesson = lesson;
        this.stem = stem;
        this.options = new ArrayList<>(options);
        this.answerIndex = answerIndex;
        this.explanation = explanation;
    }

    public Long getId() { return id; }
    public Lesson getLesson() { return lesson; }
    public String getStem() { return stem; }
    public List<String> getOptions() { return options; }
    public int getAnswerIndex() { return answerIndex; }
    public String getExplanation() { return explanation; }
}
