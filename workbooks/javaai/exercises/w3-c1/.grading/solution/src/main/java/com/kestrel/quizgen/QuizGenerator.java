package com.kestrel.quizgen;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.function.DoubleSupplier;

/** Generates quiz items for one lesson with Gemini structured output, validation and bounded retries. */
public final class QuizGenerator {

    private final Model.GeminiClient client;
    private final QuizGenConfig config;
    private final Model.Sleeper sleeper;
    private final Clock clock;
    private final DoubleSupplier jitter;
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
        Instant deadline = clock.instant().plus(config.deadline());
        String basePrompt = Prompts.userPrompt(lesson, count);
        String prompt = basePrompt;
        long in = 0, out = 0;
        int calls = 0, validityAttempts = 0, rateLimitRetries = 0;
        List<String> lastProblems = List.of();

        while (validityAttempts < config.maxValidityAttempts()) {
            Model.Request req = new Model.Request(config.model(), Prompts.SYSTEM, prompt, QuizSchema.schema(),
                    "application/json", config.temperature(), config.maxOutputTokens());
            Model.Response res;
            calls++;
            try {
                res = client.generate(req);
            } catch (Model.RateLimitedException e) {
                if (rateLimitRetries >= config.maxRateLimitRetries())
                    return new GenerationResult.Failed(List.of("rate limited: gave up after " + calls + " calls"), calls, usage(in, out));
                Duration delay = backoff(rateLimitRetries++, e.retryAfter());
                if (clock.instant().plus(delay).isAfter(deadline))
                    return new GenerationResult.Failed(List.of("deadline of " + config.deadline().toSeconds() + " s would be exceeded while rate limited"), calls, usage(in, out));
                sleeper.sleep(delay);
                continue;
            }
            in += res.inputTokens();
            out += res.outputTokens();
            validityAttempts++;

            if (res.finishReason() == Model.FinishReason.SAFETY || res.finishReason() == Model.FinishReason.RECITATION)
                return new GenerationResult.Blocked("finishReason " + res.finishReason(), calls, usage(in, out));

            List<String> problems = new ArrayList<>();
            List<QuizItem> items = null;
            if (res.finishReason() == Model.FinishReason.MAX_TOKENS) {
                problems.add("the answer was cut off at the output token limit; return shorter explanations");
            } else {
                try {
                    Envelope env = json.readValue(res.text(), Envelope.class);
                    items = env.items();
                    problems.addAll(validator.validate(items, lesson, count));
                } catch (Exception e) {
                    problems.add("the answer was not valid JSON for the schema: " + firstLine(e.getMessage()));
                }
            }
            if (problems.isEmpty()) return new GenerationResult.Success(List.copyOf(items), calls, usage(in, out));
            lastProblems = problems;
            prompt = basePrompt + "\n\nYour previous answer was rejected for these reasons:\n- "
                    + String.join("\n- ", problems) + "\nReturn the complete corrected JSON.";
            if (clock.instant().isAfter(deadline))
                return new GenerationResult.Failed(List.of("deadline exceeded"), calls, usage(in, out));
        }
        return new GenerationResult.Failed(lastProblems, calls, usage(in, out));
    }

    /** Full jitter: uniform(0, min(cap, base * 2^n)); a server Retry-After is a floor. */
    private Duration backoff(int n, Duration retryAfter) {
        long ceiling = Math.min(config.maxBackoff().toMillis(), config.baseBackoff().toMillis() << Math.min(n, 20));
        Duration d = Duration.ofMillis((long) (ceiling * jitter.getAsDouble()));
        if (retryAfter != null && retryAfter.compareTo(d) > 0) d = retryAfter;
        return d;
    }

    private GenerationResult.Usage usage(long in, long out) {
        double cost = in * config.inputPricePerMillion() / 1e6 + out * config.outputPricePerMillion() / 1e6;
        return new GenerationResult.Usage(in, out, cost);
    }

    private static String firstLine(String s) {
        if (s == null) return "";
        int i = s.indexOf('\n');
        return i < 0 ? s : s.substring(0, i);
    }

    /** The JSON envelope the schema describes. */
    record Envelope(List<QuizItem> items) { }
}
