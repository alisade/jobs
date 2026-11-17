package com.kestrel.catalog.api;

import com.kestrel.catalog.api.Dtos.*;
import com.kestrel.catalog.api.ApiErrors.BadRequest;
import com.kestrel.catalog.api.ApiErrors.Conflict;
import com.kestrel.catalog.api.ApiErrors.NotFound;
import com.kestrel.catalog.domain.*;
import java.net.URI;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class CatalogController {

    private final CourseRepository courses;
    private final LessonRepository lessons;
    private final QuizItemRepository quizItems;
    private final QuizAttemptRepository attempts;

    public CatalogController(CourseRepository courses, LessonRepository lessons,
                             QuizItemRepository quizItems, QuizAttemptRepository attempts) {
        this.courses = courses;
        this.lessons = lessons;
        this.quizItems = quizItems;
        this.attempts = attempts;
    }

    static final int MAX_PAGE_SIZE = 50;

    // ---------------------------------------------------------------- courses

    @PostMapping("/courses")
    @Transactional
    public ResponseEntity<CourseView> createCourse(@Valid @RequestBody CreateCourse req) {
        if (courses.findBySlug(req.slug()).isPresent()) throw new Conflict("Course slug already exists: " + req.slug());
        Course saved = courses.saveAndFlush(new Course(req.slug(), req.title(), req.level()));
        return ResponseEntity.created(URI.create("/api/courses/" + saved.getSlug())).body(view(saved));
    }

    @GetMapping("/courses/{slug}")
    @Transactional(readOnly = true)
    public CourseView getCourse(@PathVariable String slug) {
        return view(course(slug));
    }

    @GetMapping("/courses")
    @Transactional(readOnly = true)
    public PageView<CourseView> listCourses(@RequestParam(defaultValue = "PUBLISHED") CourseStatus status,
                                            @RequestParam(defaultValue = "0") int page,
                                            @RequestParam(defaultValue = "20") int size) {
        if (page < 0) throw new BadRequest("page must be >= 0");
        if (size < 1) throw new BadRequest("size must be >= 1");
        size = Math.min(size, MAX_PAGE_SIZE);
        Page<Course> result = courses.findByStatus(status, PageRequest.of(page, size, Sort.by("title", "id")));
        return new PageView<>(result.map(this::view).getContent(), page, size, result.getTotalElements());
    }

    @PostMapping("/courses/{slug}/publish")
    @Transactional
    public CourseView publish(@PathVariable String slug) {
        Course course = course(slug);
        course.setStatus(CourseStatus.PUBLISHED);
        return view(course);
    }

    // ---------------------------------------------------------------- lessons

    @PostMapping("/courses/{slug}/lessons")
    @Transactional
    public ResponseEntity<LessonView> createLesson(@PathVariable String slug, @Valid @RequestBody CreateLesson req) {
        Course course = course(slug);
        Lesson saved = lessons.saveAndFlush(new Lesson(course, req.position(), req.title()));
        return ResponseEntity.created(URI.create("/api/lessons/" + saved.getId()))
                .body(new LessonView(saved.getId(), course.getSlug(), saved.getPosition(), saved.getTitle()));
    }

    // ---------------------------------------------------------------- quiz items

    @PostMapping("/lessons/{lessonId}/quiz-items")
    @Transactional
    public ResponseEntity<QuizItemAuthorView> createQuizItem(@PathVariable Long lessonId, @Valid @RequestBody CreateQuizItem req) {
        Lesson lesson = lessons.findById(lessonId).orElseThrow(() -> new NotFound("No lesson " + lessonId));
        QuizItem saved = quizItems.saveAndFlush(
                new QuizItem(lesson, req.stem(), req.options(), req.answerIndex(), req.explanation()));
        return ResponseEntity.created(URI.create("/api/quiz-items/" + saved.getId()))
                .body(new QuizItemAuthorView(saved.getId(), lessonId, saved.getStem(), List.copyOf(saved.getOptions()),
                        saved.getAnswerIndex(), saved.getExplanation()));
    }

    @GetMapping("/lessons/{lessonId}/quiz-items")
    @Transactional(readOnly = true)
    public List<QuizItemLearnerView> learnerQuiz(@PathVariable Long lessonId) {
        return quizItems.findByLessonIdOrderById(lessonId).stream()
                .map(q -> new QuizItemLearnerView(q.getId(), q.getStem(), List.copyOf(q.getOptions())))
                .toList();
    }

    @PostMapping("/quiz-items/{id}/attempts")
    @Transactional
    public ResponseEntity<AttemptResult> submit(@PathVariable Long id, @Valid @RequestBody SubmitAttempt req) {
        QuizItem item = quizItems.findById(id).orElseThrow(() -> new NotFound("No quiz item " + id));
        if (req.chosenIndex() >= item.getOptions().size()) throw new BadRequest("chosenIndex is not one of the options");
        boolean correct = req.chosenIndex() == item.getAnswerIndex();
        QuizAttempt saved = attempts.save(new QuizAttempt(item, req.learnerId(), req.chosenIndex(), correct));
        return ResponseEntity.status(201).body(new AttemptResult(saved.getId(), correct, item.getExplanation()));
    }

    private Course course(String slug) {
        return courses.findBySlug(slug).orElseThrow(() -> new NotFound("No course " + slug));
    }

    private CourseView view(Course c) {
        return new CourseView(c.getId(), c.getSlug(), c.getTitle(), c.getLevel().name(), c.getStatus().name());
    }
}
