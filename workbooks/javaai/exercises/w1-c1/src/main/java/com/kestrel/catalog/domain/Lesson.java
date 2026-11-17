package com.kestrel.catalog.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "lesson")
public class Lesson {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "course_id", nullable = false)
    private Course course;

    @Column(nullable = false)
    private int position;

    @Column(nullable = false, length = 200)
    private String title;

    protected Lesson() { }

    public Lesson(Course course, int position, String title) {
        this.course = course;
        this.position = position;
        this.title = title;
    }

    public Long getId() { return id; }
    public Course getCourse() { return course; }
    public int getPosition() { return position; }
    public String getTitle() { return title; }
}
