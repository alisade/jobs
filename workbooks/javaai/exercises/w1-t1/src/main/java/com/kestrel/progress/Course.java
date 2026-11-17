package com.kestrel.progress;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "course")
public class Course {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(nullable = false) private String slug;
    @Column(nullable = false) private String title;

    @OneToMany(mappedBy = "course")
    @OrderBy("position")
    private List<Lesson> lessons = new ArrayList<>();

    protected Course() { }
    public Course(String slug, String title) { this.slug = slug; this.title = title; }

    public Long getId() { return id; }
    public String getSlug() { return slug; }
    public String getTitle() { return title; }
    public List<Lesson> getLessons() { return lessons; }
}
