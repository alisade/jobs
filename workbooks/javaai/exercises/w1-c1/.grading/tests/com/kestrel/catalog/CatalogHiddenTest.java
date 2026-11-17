package com.kestrel.catalog;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataAccessException;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class CatalogHiddenTest {

    static final String V1_SHA256 = "c36b1d0ca12a4e8501c273f9311362ed4fb5d62662c73739129b628914fc03c4";
    static final AtomicInteger SEQ = new AtomicInteger();

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @Autowired JdbcTemplate jdbc;

    // ------------------------------------------------------------ helpers

    private MvcResult postJson(String url, String body) throws Exception {
        return mvc.perform(post(url).contentType(MediaType.APPLICATION_JSON).content(body)).andReturn();
    }

    private String newCourse() throws Exception {
        String slug = "course-" + SEQ.incrementAndGet();
        MvcResult r = postJson("/api/courses", "{\"slug\":\"" + slug + "\",\"title\":\"Course " + slug + "\",\"level\":\"BEGINNER\"}");
        assertEquals(201, r.getResponse().getStatus(), r.getResponse().getContentAsString());
        return slug;
    }

    private long newLesson(String slug, int position) throws Exception {
        MvcResult r = postJson("/api/courses/" + slug + "/lessons", "{\"title\":\"Lesson " + position + "\",\"position\":" + position + "}");
        assertEquals(201, r.getResponse().getStatus(), r.getResponse().getContentAsString());
        return json.readTree(r.getResponse().getContentAsString()).get("id").asLong();
    }

    private long newItem(long lessonId) throws Exception {
        MvcResult r = postJson("/api/lessons/" + lessonId + "/quiz-items",
                "{\"stem\":\"Which organelle makes ATP?\",\"options\":[\"Mitochondrion\",\"Ribosome\",\"Golgi body\"],"
                        + "\"answerIndex\":0,\"explanation\":\"Section 2.1: oxidative phosphorylation.\"}");
        assertEquals(201, r.getResponse().getStatus(), r.getResponse().getContentAsString());
        return json.readTree(r.getResponse().getContentAsString()).get("id").asLong();
    }

    private JsonNode problem(MvcResult r, int status) throws Exception {
        assertEquals(status, r.getResponse().getStatus(), r.getResponse().getContentAsString());
        String ct = r.getResponse().getContentType();
        assertNotNull(ct, "problem responses need a content type");
        assertTrue(ct.startsWith("application/problem+json"), "expected application/problem+json, got " + ct);
        JsonNode body = json.readTree(r.getResponse().getContentAsString());
        assertEquals(status, body.path("status").asInt(), "problem detail must carry the status");
        return body;
    }

    private void assertFieldError(JsonNode body, String field) {
        JsonNode errors = body.path("errors");
        assertTrue(errors.isArray() && errors.size() > 0, "problem detail needs an 'errors' array, got " + body);
        boolean found = false;
        for (JsonNode e : errors) if (field.equals(e.path("field").asText())) found = true;
        assertTrue(found, "expected a field error for '" + field + "' in " + errors);
    }

    // ------------------------------------------------------------ courses

    @Test
    void invalidSlugIs400WithFieldError() throws Exception {
        JsonNode p = problem(postJson("/api/courses", "{\"slug\":\"Intro To Stats\",\"title\":\"x\",\"level\":\"BEGINNER\"}"), 400);
        assertFieldError(p, "slug");
    }

    @Test
    void blankTitleAndMissingLevelAre400() throws Exception {
        JsonNode p = problem(postJson("/api/courses", "{\"slug\":\"blank-title\",\"title\":\"  \"}"), 400);
        assertFieldError(p, "title");
        assertFieldError(p, "level");
    }

    @Test
    void unknownLevelIs400NotServerError() throws Exception {
        problem(postJson("/api/courses", "{\"slug\":\"expert-course\",\"title\":\"x\",\"level\":\"EXPERT\"}"), 400);
    }

    @Test
    void duplicateSlugIs409Problem() throws Exception {
        String slug = newCourse();
        problem(postJson("/api/courses", "{\"slug\":\"" + slug + "\",\"title\":\"Again\",\"level\":\"BEGINNER\"}"), 409);
    }

    @Test
    void unknownCourseIs404Problem() throws Exception {
        problem(mvc.perform(get("/api/courses/no-such-course")).andReturn(), 404);
        problem(postJson("/api/courses/no-such-course/lessons", "{\"title\":\"x\",\"position\":1}"), 404);
    }

    @Test
    void pageSizeIsCappedAndPageValidated() throws Exception {
        mvc.perform(get("/api/courses?status=DRAFT&size=500"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.size").value(50));
        problem(mvc.perform(get("/api/courses?page=-1")).andReturn(), 400);
    }

    // ------------------------------------------------------------ lessons and items

    @Test
    void duplicateLessonPositionIs409() throws Exception {
        String slug = newCourse();
        newLesson(slug, 1);
        problem(postJson("/api/courses/" + slug + "/lessons", "{\"title\":\"Another first\",\"position\":1}"), 409);
        problem(postJson("/api/courses/" + slug + "/lessons", "{\"title\":\"Zero\",\"position\":0}"), 400);
    }

    @Test
    void quizItemNeedsTwoToSixDistinctOptions() throws Exception {
        long lesson = newLesson(newCourse(), 1);
        String url = "/api/lessons/" + lesson + "/quiz-items";
        assertFieldError(problem(postJson(url, "{\"stem\":\"s\",\"options\":[\"only\"],\"answerIndex\":0,\"explanation\":\"e\"}"), 400), "options");
        assertFieldError(problem(postJson(url, "{\"stem\":\"s\",\"options\":[\"a\",\"b\",\"c\",\"d\",\"e\",\"f\",\"g\"],\"answerIndex\":0,\"explanation\":\"e\"}"), 400), "options");
        assertFieldError(problem(postJson(url, "{\"stem\":\"s\",\"options\":[\"Paris\",\"paris \",\"Rome\"],\"answerIndex\":0,\"explanation\":\"e\"}"), 400), "options");
    }

    @Test
    void answerIndexOutOfRangeIs400() throws Exception {
        long lesson = newLesson(newCourse(), 1);
        JsonNode p = problem(postJson("/api/lessons/" + lesson + "/quiz-items",
                "{\"stem\":\"s\",\"options\":[\"a\",\"b\",\"c\"],\"answerIndex\":3,\"explanation\":\"e\"}"), 400);
        assertFieldError(p, "answerIndex");
    }

    @Test
    void learnerViewNeverCarriesTheKey() throws Exception {
        long lesson = newLesson(newCourse(), 1);
        newItem(lesson);
        String body = mvc.perform(get("/api/lessons/" + lesson + "/quiz-items")).andReturn().getResponse().getContentAsString();
        JsonNode item = json.readTree(body).get(0);
        assertFalse(item.has("answerIndex"), "learner view leaks answerIndex: " + body);
        assertFalse(item.has("explanation"), "learner view leaks the explanation before an attempt: " + body);
        assertTrue(item.has("stem") && item.has("options") && item.has("id"));
    }

    // ------------------------------------------------------------ attempts

    @Test
    void attemptIsScoredAndValidated() throws Exception {
        long item = newItem(newLesson(newCourse(), 1));
        MvcResult ok = postJson("/api/quiz-items/" + item + "/attempts", "{\"learnerId\":\"lrn-1\",\"chosenIndex\":0}");
        assertEquals(201, ok.getResponse().getStatus());
        assertTrue(json.readTree(ok.getResponse().getContentAsString()).get("correct").asBoolean());
        problem(postJson("/api/quiz-items/" + item + "/attempts", "{\"learnerId\":\"lrn-1\",\"chosenIndex\":7}"), 400);
        assertFieldError(problem(postJson("/api/quiz-items/" + item + "/attempts", "{\"learnerId\":\"\",\"chosenIndex\":1}"), 400), "learnerId");
        problem(postJson("/api/quiz-items/999999/attempts", "{\"learnerId\":\"lrn-1\",\"chosenIndex\":0}"), 404);
    }

    // ------------------------------------------------------------ schema

    @Test
    void appliedMigrationUntouchedAndNewMigrationAdded() throws Exception {
        byte[] v1 = Files.readAllBytes(Path.of("src/main/resources/db/migration/V1__catalog.sql"));
        String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(v1));
        assertEquals(V1_SHA256, sha, "V1__catalog.sql was edited; it is already applied everywhere. Add a V2 migration.");
        Integer applied = jdbc.queryForObject("select count(*) from \"flyway_schema_history\" where \"success\" = true and \"version\" is not null and \"version\" <> '1'", Integer.class);
        assertTrue(applied != null && applied >= 1, "expected at least one migration after V1, got " + applied);
    }

    @Test
    void databaseEnforcesUniquenessAndForeignKeys() {
        jdbc.update("insert into course(slug, title, level, status, created_at) values ('db-unique', 't', 'BEGINNER', 'DRAFT', current_timestamp)");
        assertThrows(DataAccessException.class, () ->
                jdbc.update("insert into course(slug, title, level, status, created_at) values ('db-unique', 't2', 'BEGINNER', 'DRAFT', current_timestamp)"),
                "course.slug must be unique in the database, not only in the API");
        assertThrows(DataAccessException.class, () ->
                jdbc.update("insert into lesson(course_id, position, title) values (987654, 1, 'orphan')"),
                "lesson.course_id needs a foreign key");
        Long courseId = jdbc.queryForObject("select id from course where slug = 'db-unique'", Long.class);
        jdbc.update("insert into lesson(course_id, position, title) values (?, 1, 'one')", courseId);
        assertThrows(DataAccessException.class, () ->
                jdbc.update("insert into lesson(course_id, position, title) values (?, 1, 'one again')", courseId),
                "(course_id, position) must be unique");
    }

    @Test
    void databaseEnforcesQuizRules() {
        jdbc.update("insert into course(slug, title, level, status, created_at) values ('db-quiz', 't', 'BEGINNER', 'DRAFT', current_timestamp)");
        Long courseId = jdbc.queryForObject("select id from course where slug = 'db-quiz'", Long.class);
        jdbc.update("insert into lesson(course_id, position, title) values (?, 1, 'one')", courseId);
        Long lessonId = jdbc.queryForObject("select id from lesson where course_id = ?", Long.class, courseId);
        assertThrows(DataAccessException.class, () ->
                jdbc.update("insert into quiz_item(lesson_id, stem, answer_index, explanation) values (?, 's', -1, 'e')", lessonId),
                "answer_index needs a CHECK constraint (>= 0)");
        assertThrows(DataAccessException.class, () ->
                jdbc.update("insert into quiz_attempt(quiz_item_id, learner_id, chosen_index, correct, created_at) values (424242, 'l', 0, false, current_timestamp)"),
                "quiz_attempt.quiz_item_id needs a foreign key");
    }

    @Test
    void attemptsAreIndexedByLearner() {
        Integer n = jdbc.queryForObject(
                "select count(*) from information_schema.index_columns where lower(table_name) = 'quiz_attempt' "
                        + "and lower(column_name) = 'learner_id' and ordinal_position = 1", Integer.class);
        assertTrue(n != null && n > 0, "add an index that starts with quiz_attempt.learner_id (progress queries filter by learner)");
    }
}
