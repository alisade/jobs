package com.kestrel.progress;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.EntityManagerFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class ProgressHiddenTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @Autowired JdbcTemplate jdbc;
    @Autowired EntityManagerFactory emf;

    @BeforeAll
    void seed() {
        Seed.learner(jdbc, "lrn-few", "few", 2, 3);
        Seed.learner(jdbc, "lrn-many", "many", 8, 15);
    }

    private Statistics stats() {
        Statistics s = emf.unwrap(SessionFactory.class).getStatistics();
        s.setStatisticsEnabled(true);
        return s;
    }

    private JsonNode get(String learner) throws Exception {
        var res = mvc.perform(MockMvcRequestBuilders.get("/api/learners/" + learner + "/progress")).andReturn().getResponse();
        assertEquals(200, res.getStatus(), res.getContentAsString());
        return json.readTree(res.getContentAsString());
    }

    private long statementsFor(String learner) throws Exception {
        Statistics s = stats();
        s.clear();
        get(learner);
        return s.getPrepareStatementCount();
    }

    @Test
    void boundedStatementsPerRequest() throws Exception {
        long n = statementsFor("lrn-many");
        assertTrue(n <= 4, "progress for 8 courses x 15 lessons ran " + n + " SQL statements; expected a constant handful (<= 4)");
    }

    @Test
    void statementCountDoesNotGrowWithData() throws Exception {
        long few = statementsFor("lrn-few");
        long many = statementsFor("lrn-many");
        assertEquals(few, many, "statement count must not depend on courses/lessons (few=" + few + ", many=" + many + ")");
    }

    @Test
    void numbersAreStillRightForALargeLearner() throws Exception {
        JsonNode courses = get("lrn-many").get("courses");
        assertEquals(8, courses.size());
        for (int i = 0; i < 8; i++) {
            JsonNode c = courses.get(i);
            assertEquals("many-course-" + (i + 1), c.get("slug").asText(), "courses ordered by enrollment date");
            assertEquals(15, c.get("lessonsTotal").asInt());
            // lessons with k % 3 != 0 and k even end correct: 2, 4, 8, 10, 14 -> 5 of 15
            assertEquals(5, c.get("lessonsMastered").asInt());
            assertEquals(33.3, c.get("percentComplete").asDouble(), 0.001);
            JsonNode lessons = c.get("lessons");
            for (int k = 1; k <= 15; k++) {
                JsonNode l = lessons.get(k - 1);
                assertEquals(k, l.get("position").asInt(), "lessons ordered by position");
                assertEquals(k % 3, l.get("attempts").asInt(), "attempts for lesson " + k + " (other learners must not count)");
                boolean mastered = k % 3 != 0 && k % 2 == 0;
                assertEquals(mastered ? 1 : 0, l.get("correct").asInt(), "correct count for lesson " + k);
                assertEquals(mastered, l.get("mastered").asBoolean());
            }
        }
    }

    @Test
    void lessonsWithoutAttemptsAreStillListed() throws Exception {
        JsonNode lessons = get("lrn-few").get("courses").get(0).get("lessons");
        assertEquals(3, lessons.size());
        assertEquals(0, lessons.get(2).get("attempts").asInt(), "lesson 3 has no attempts but must appear");
        assertEquals("Lesson 3", lessons.get(2).get("title").asText());
    }

    @Test
    void unknownLearnerGetsEmptyProgress() throws Exception {
        JsonNode body = get("nobody");
        assertEquals("nobody", body.get("learnerId").asText());
        assertEquals(0, body.get("courses").size());
    }

    @Test
    void poolSizeWasNotTheFix() throws Exception {
        Properties p = new Properties();
        p.load(Files.newBufferedReader(Path.of("src/main/resources/application.properties")));
        int pool = Integer.parseInt(p.getProperty("spring.datasource.hikari.maximum-pool-size", "10").trim());
        assertTrue(pool <= 10, "maximum-pool-size raised to " + pool + ": 4 instances x " + pool
                + " connections against a 100-connection Cloud SQL instance treats the symptom and risks the database");
    }

    @Test
    void attemptsByLearnerAreIndexed() {
        Integer n = jdbc.queryForObject(
                "select count(*) from information_schema.index_columns where lower(table_name) = 'quiz_attempt' "
                        + "and lower(column_name) = 'learner_id' and ordinal_position = 1", Integer.class);
        assertTrue(n != null && n > 0, "the replacement query filters quiz_attempt by learner_id: add an index that starts with it (new migration)");
    }
}
