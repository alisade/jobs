package com.kestrel.progress;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
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

/** Visible: the endpoint returns the right numbers for a small learner. */
@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class ProgressVisibleTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @Autowired JdbcTemplate jdbc;

    @BeforeAll
    void seed() { Seed.learner(jdbc, "lrn-small", "vis", 2, 4); }

    @Test
    void smallLearnerProgress() throws Exception {
        String body = mvc.perform(MockMvcRequestBuilders.get("/api/learners/lrn-small/progress"))
                .andReturn().getResponse().getContentAsString();
        JsonNode courses = json.readTree(body).get("courses");
        assertEquals(2, courses.size());
        JsonNode c1 = courses.get(0);
        assertEquals("vis-course-1", c1.get("slug").asText());
        assertEquals(4, c1.get("lessonsTotal").asInt());
        // lessons 1..4 get 1, 2, 0, 1 attempts; lessons 2 and 4 end with a correct attempt
        assertEquals(2, c1.get("lessonsMastered").asInt());
        assertEquals(50.0, c1.get("percentComplete").asDouble());
        assertEquals(1, c1.get("lessons").get(0).get("position").asInt());
    }
}
