package com.kestrel.quizgen;

import java.time.Duration;

/**
 * Tunables. Prices are USD per 1M tokens (illustrative; check the pricing page for the model you pin).
 */
public record QuizGenConfig(String model, double temperature, int maxOutputTokens,
                            int maxValidityAttempts, int maxRateLimitRetries,
                            Duration baseBackoff, Duration maxBackoff, Duration deadline,
                            double inputPricePerMillion, double outputPricePerMillion) {

    public static QuizGenConfig defaults() {
        return new QuizGenConfig("gemini-2.5-flash", 0.2, 4096, 3, 4,
                Duration.ofMillis(500), Duration.ofSeconds(8), Duration.ofSeconds(20), 0.30, 2.50);
    }
}
