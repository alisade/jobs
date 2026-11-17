package com.kestrel.quizgen;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Clock;
import java.util.List;
import java.util.function.DoubleSupplier;

/**
 * Generates quiz items for one lesson with Gemini structured output.
 *
 * TODO(w3-c1): this is the prototype from the hackathon. It calls the model once, trusts the JSON,
 * and lets a 429 escape. Implement the behaviour in README "Requirements".
 */
public final class QuizGenerator {

    private final Model.GeminiClient client;
    private final QuizGenConfig config;
    private final Model.Sleeper sleeper;
    private final Clock clock;
    private final DoubleSupplier jitter; // uniform in [0, 1)
    private final QuizValidator validator = new QuizValidator();
    private final ObjectMapper json = new ObjectMapper();

    public QuizGenerator(Model.GeminiClient client, QuizGenConfig config, Model.Sleeper sleeper, Clock clock, DoubleSupplier jitter) {
        this.client = client;
        this.config = config;
        this.sleeper = sleeper;
        this.clock = clock;
        this.jitter = jitter;
    }

    public GenerationResult generate(Model.Lesson lesson, int count) {
        String prompt = Prompts.userPrompt(lesson, count);
        Model.Request req = new Model.Request(config.model(), Prompts.SYSTEM, prompt, null, "text/plain", 1.0, 512);
        try {
            Model.Response res = client.generate(req);
            Envelope env = json.readValue(res.text(), Envelope.class);
            return new GenerationResult.Success(env.items(), 1, GenerationResult.Usage.ZERO);
        } catch (Model.RateLimitedException e) {
            throw new IllegalStateException(e);
        } catch (Exception e) {
            return new GenerationResult.Failed(List.of(e.getMessage()), 1, GenerationResult.Usage.ZERO);
        }
    }

    /** The JSON envelope the schema describes. */
    record Envelope(List<QuizItem> items) { }
}
