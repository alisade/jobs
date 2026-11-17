package com.kestrel.quizgen;

import java.util.List;
import java.util.Map;

/** The response schema sent with every request, so Gemini's controlled generation returns this shape. */
public final class QuizSchema {
    private QuizSchema() { }

    private static final Map<String, Object> ITEM = Map.of(
            "type", "OBJECT",
            "properties", Map.of(
                    "stem", Map.of("type", "STRING"),
                    "options", Map.of("type", "ARRAY", "items", Map.of("type", "STRING"), "minItems", 4, "maxItems", 4),
                    "answerIndex", Map.of("type", "INTEGER"),
                    "explanation", Map.of("type", "STRING"),
                    "sectionId", Map.of("type", "STRING")),
            "required", List.of("stem", "options", "answerIndex", "explanation", "sectionId"),
            "propertyOrdering", List.of("stem", "options", "answerIndex", "explanation", "sectionId"));

    private static final Map<String, Object> SCHEMA = Map.of(
            "type", "OBJECT",
            "properties", Map.of("items", Map.of("type", "ARRAY", "items", ITEM)),
            "required", List.of("items"));

    public static Map<String, Object> schema() {
        return SCHEMA;
    }
}
