package com.kestrel.quizgen;

import java.util.List;

/** What the endpoint gets back. Never an exception for model behaviour: callers switch on the type. */
public sealed interface GenerationResult {
    Usage usage();

    record Success(List<QuizItem> items, int modelCalls, Usage usage) implements GenerationResult { }

    /** The model refused or was filtered (SAFETY, RECITATION). Not retried. */
    record Blocked(String reason, int modelCalls, Usage usage) implements GenerationResult { }

    /** Gave up: invalid output after the allowed attempts, rate limits, or the deadline. */
    record Failed(List<String> errors, int modelCalls, Usage usage) implements GenerationResult { }

    record Usage(long inputTokens, long outputTokens, double costUsd) {
        public static final Usage ZERO = new Usage(0, 0, 0.0);
    }
}
