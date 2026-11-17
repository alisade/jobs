package com.kestrel.catalog;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;

/** Visible tests: the happy path. The grader adds hidden tests for validation, errors and schema. */
@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class CatalogHappyPathTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;

    @Test
    void createAndFetchCourse() throws Exception {
        mvc.perform(post("/api/courses").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"slug\":\"intro-to-statistics\",\"title\":\"Intro to Statistics\",\"level\":\"BEGINNER\"}"))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/api/courses/intro-to-statistics"))
                .andExpect(jsonPath("$.status").value("DRAFT"));

        mvc.perform(get("/api/courses/intro-to-statistics"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Intro to Statistics"));
    }

    @Test
    void lessonAndQuizItem() throws Exception {
        mvc.perform(post("/api/courses").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"slug\":\"cell-biology\",\"title\":\"Cell Biology\",\"level\":\"INTERMEDIATE\"}"))
                .andExpect(status().isCreated());
        String lesson = mvc.perform(post("/api/courses/cell-biology/lessons").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"The membrane\",\"position\":1}"))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        long lessonId = json.readTree(lesson).get("id").asLong();

        mvc.perform(post("/api/lessons/" + lessonId + "/quiz-items").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"stem\":\"What is the membrane mostly made of?\","
                                + "\"options\":[\"Phospholipids\",\"Cellulose\",\"Keratin\",\"Chitin\"],"
                                + "\"answerIndex\":0,\"explanation\":\"Section 1.2: a phospholipid bilayer.\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.answerIndex").value(0));

        String quiz = mvc.perform(get("/api/lessons/" + lessonId + "/quiz-items"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        JsonNode items = json.readTree(quiz);
        org.junit.jupiter.api.Assertions.assertEquals(1, items.size());
        org.junit.jupiter.api.Assertions.assertEquals(4, items.get(0).get("options").size());
    }
}
