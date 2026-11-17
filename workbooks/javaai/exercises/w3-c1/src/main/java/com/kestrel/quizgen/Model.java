package com.kestrel.quizgen;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * The slice of the Gemini generateContent contract this service uses. In production
 * {@link GeminiClient} is backed by the Google Gen AI Java SDK (com.google.genai) against Vertex AI;
 * tests use a scripted fake. Do not change these types.
 */
public final class Model {
    private Model() { }

    public enum FinishReason { STOP, MAX_TOKENS, SAFETY, RECITATION, OTHER }

    /** responseSchema uses the OpenAPI-subset JSON schema Gemini accepts (type, properties, items, required, enum, minItems, maxItems). */
    public record Request(String model, String systemInstruction, String prompt, Map<String, Object> responseSchema,
                          String responseMimeType, double temperature, int maxOutputTokens) { }

    public record Response(String text, FinishReason finishReason, int inputTokens, int outputTokens) { }

    /** HTTP 429 RESOURCE_EXHAUSTED from Standard PayGo. retryAfter may be null. */
    public static class RateLimitedException extends Exception {
        private final Duration retryAfter;
        public RateLimitedException(Duration retryAfter) { super("429 RESOURCE_EXHAUSTED"); this.retryAfter = retryAfter; }
        public Duration retryAfter() { return retryAfter; }
    }

    public interface GeminiClient {
        Response generate(Request request) throws RateLimitedException;
    }

    public interface Sleeper {
        void sleep(Duration d);
    }

    public record Section(String id, String heading, String text) { }

    public record Lesson(String id, String title, List<Section> sections) { }
}
