package com.kestrel.quizgen;

import java.util.Map;

/** The response schema sent with every request, so Gemini's controlled generation returns this shape. */
public final class QuizSchema {
    private QuizSchema() { }

    /**
     * TODO(w3-c1): describe {"items": [{"stem", "options" (exactly 4 strings), "answerIndex" (integer),
     * "explanation", "sectionId"}]} with every field required. Use Map.of / List.of.
     */
    public static Map<String, Object> schema() {
        return Map.of("type", "OBJECT");
    }
}
