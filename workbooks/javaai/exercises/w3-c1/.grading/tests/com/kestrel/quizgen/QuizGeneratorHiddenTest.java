package com.kestrel.quizgen;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

@Timeout(10)
class QuizGeneratorHiddenTest {

    private final FakeGemini.TestTime time = new FakeGemini.TestTime();

    private GenerationResult run(FakeGemini fake, int count) {
        return new QuizGenerator(fake, QuizGenConfig.defaults(), time, time.clock(), () -> 0.5).generate(Fixtures.LESSON, count);
    }

    private static String joined(List<String> problems) { return String.join(" | ", problems).toLowerCase(Locale.ROOT); }

    private static List<String> check(QuizItem item) {
        return new QuizValidator().validate(List.of(item), Fixtures.LESSON, 1);
    }

    private static final List<String> FOUR = List.of("A phospholipid bilayer", "A cellulose wall", "A protein sheet", "A starch lattice");

    // ------------------------------------------------------------ request

    @Test
    void requestUsesJsonModeSchemaAndPinnedModel() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.ok(Fixtures.VALID3));
        run(fake, 3);
        Model.Request req = fake.requests.get(0);
        assertEquals("application/json", req.responseMimeType());
        assertNotNull(req.responseSchema(), "send the response schema");
        assertEquals(QuizSchema.schema(), req.responseSchema());
        assertEquals(QuizGenConfig.defaults().model(), req.model());
        assertTrue(req.temperature() <= 0.4, "quiz generation wants low temperature, got " + req.temperature());
        assertTrue(req.maxOutputTokens() >= 1024, "512 output tokens truncates a 5-item quiz");
        assertTrue(req.prompt().contains("[section s2]"), "the lesson text must be in the prompt");
    }

    @Test
    @SuppressWarnings("unchecked")
    void schemaDescribesTheEnvelope() {
        Map<String, Object> s = QuizSchema.schema();
        assertTrue("object".equalsIgnoreCase(String.valueOf(s.get("type"))));
        Map<String, Object> props = (Map<String, Object>) s.get("properties");
        assertNotNull(props, "top-level properties");
        Map<String, Object> items = (Map<String, Object>) props.get("items");
        assertTrue("array".equalsIgnoreCase(String.valueOf(items.get("type"))));
        assertTrue(((List<String>) s.get("required")).contains("items"));
        Map<String, Object> item = (Map<String, Object>) items.get("items");
        Map<String, Object> ip = (Map<String, Object>) item.get("properties");
        assertEquals(Set5.FIELDS, new java.util.TreeSet<>(ip.keySet()));
        assertEquals(Set5.FIELDS, new java.util.TreeSet<>((List<String>) item.get("required")));
        Map<String, Object> options = (Map<String, Object>) ip.get("options");
        assertTrue("array".equalsIgnoreCase(String.valueOf(options.get("type"))));
        assertEquals(4, ((Number) options.get("minItems")).intValue());
        assertEquals(4, ((Number) options.get("maxItems")).intValue());
        assertTrue("integer".equalsIgnoreCase(String.valueOf(((Map<String, Object>) ip.get("answerIndex")).get("type"))));
    }

    static final class Set5 {
        static final java.util.TreeSet<String> FIELDS = new java.util.TreeSet<>(List.of("stem", "options", "answerIndex", "explanation", "sectionId"));
    }

    // ------------------------------------------------------------ validator

    @Test
    void validatorAcceptsAGoodSet() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult.Success ok = assertInstanceOf(GenerationResult.Success.class, run(fake, 3));
        assertTrue(new QuizValidator().validate(ok.items(), Fixtures.LESSON, 3).isEmpty());
    }

    @Test
    void validatorChecksCountOptionsAndIndex() {
        QuizItem good = new QuizItem("What is the basic structure?", FOUR, 0, "Section s1 says so.", "s1");
        assertFalse(new QuizValidator().validate(List.of(good), Fixtures.LESSON, 2).isEmpty(), "wrong item count");
        assertTrue(joined(check(new QuizItem("What is the basic structure?", FOUR.subList(0, 3), 0, "x", "s1"))).contains("options"));
        assertTrue(joined(check(new QuizItem("What is the basic structure?", FOUR, 4, "x", "s1"))).contains("answerindex"));
        assertTrue(joined(check(new QuizItem("What is the basic structure?", FOUR, -1, "x", "s1"))).contains("answerindex"));
        assertFalse(check(new QuizItem("What is the basic structure?", null, 0, "x", "s1")).isEmpty(), "null options must be a problem, not an NPE");
    }

    @Test
    void validatorChecksDuplicatesAndBlanks() {
        List<String> dup = List.of("Osmosis", "osmosis ", "Diffusion", "Endocytosis");
        assertTrue(joined(check(new QuizItem("Which process moves water?", dup, 0, "x", "s3"))).contains("duplicate"));
        assertTrue(joined(check(new QuizItem("What is the basic structure?", FOUR, 0, "  ", "s1"))).contains("explanation"));
        assertTrue(joined(check(new QuizItem(" ", FOUR, 0, "x", "s1"))).contains("stem"));
        QuizItem a = new QuizItem("What is the basic structure?", FOUR, 0, "x", "s1");
        QuizItem b = new QuizItem("what is the basic structure?", FOUR, 1, "y", "s1");
        assertTrue(joined(new QuizValidator().validate(List.of(a, b), Fixtures.LESSON, 2)).contains("duplicate"));
    }

    @Test
    void validatorChecksGroundingAndGiveaways() {
        assertTrue(joined(check(new QuizItem("What is the basic structure?", FOUR, 0, "x", "s9"))).contains("sectionid"));
        List<String> problems = check(new QuizItem("Is a phospholipid bilayer the basic structure?", FOUR, 0, "x", "s1"));
        assertFalse(problems.isEmpty(), "the stem contains the correct option's wording: a giveaway");
    }

    // ------------------------------------------------------------ retries

    @Test
    void invalidJsonIsRetriedWithFeedback() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.ok("{\"items\": [ {\"stem\": "), FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult.Success ok = assertInstanceOf(GenerationResult.Success.class, run(fake, 3));
        assertEquals(2, ok.modelCalls());
        String first = fake.requests.get(0).prompt();
        String second = fake.requests.get(1).prompt();
        assertTrue(second.startsWith(first) || second.contains(first), "the corrective retry keeps the original prompt");
        assertTrue(second.length() > first.length(), "and adds what was wrong");
    }

    @Test
    void validationErrorsAreFedBack() {
        String bad = Fixtures.envelope(Fixtures.ITEM1, Fixtures.ITEM2, Fixtures.item("In osmosis, where does water move?",
                "Toward lower", "Toward higher", "Nowhere", "Into the nucleus", 7, "Section s3.", "s3"));
        FakeGemini fake = new FakeGemini(FakeGemini.Step.ok(bad), FakeGemini.Step.ok(Fixtures.VALID3));
        assertInstanceOf(GenerationResult.Success.class, run(fake, 3));
        assertTrue(fake.requests.get(1).prompt().toLowerCase(Locale.ROOT).contains("answerindex"),
                "the second prompt must name the problem (answerIndex out of range)");
    }

    @Test
    void truncatedOutputIsRetried() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.finish("{\"items\":[", Model.FinishReason.MAX_TOKENS), FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult.Success ok = assertInstanceOf(GenerationResult.Success.class, run(fake, 3));
        assertEquals(2, ok.modelCalls());
    }

    @Test
    void givesUpAfterThreeInvalidAnswers() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.ok("not json"));
        GenerationResult.Failed f = assertInstanceOf(GenerationResult.Failed.class, run(fake, 3));
        assertEquals(3, fake.requests.size(), "maxValidityAttempts is 3");
        assertEquals(3, f.modelCalls());
        assertFalse(f.errors().isEmpty());
    }

    @Test
    void safetyBlockIsNotRetried() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.finish("", Model.FinishReason.SAFETY), FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult.Blocked b = assertInstanceOf(GenerationResult.Blocked.class, run(fake, 3));
        assertEquals(1, fake.requests.size(), "a safety block is a decision, not a transient error");
        assertTrue(b.reason().toUpperCase(Locale.ROOT).contains("SAFETY"));
    }

    // ------------------------------------------------------------ rate limits

    @Test
    void rateLimitBacksOffWithJitterAndHonoursRetryAfter() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.limited(null), FakeGemini.Step.limited(null),
                FakeGemini.Step.limited(Duration.ofSeconds(3)), FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult.Success ok = assertInstanceOf(GenerationResult.Success.class, run(fake, 3));
        assertEquals(4, ok.modelCalls());
        // full jitter with jitter()=0.5: 0.5 * min(8 s, 500 ms * 2^n) -> 250 ms, 500 ms; third honours Retry-After 3 s
        assertEquals(List.of(Duration.ofMillis(250), Duration.ofMillis(500), Duration.ofSeconds(3)), time.sleeps);
    }

    @Test
    void persistentRateLimitFailsCleanly() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.limited(null));
        GenerationResult r = assertDoesNotThrow(() -> run(fake, 3));
        GenerationResult.Failed f = assertInstanceOf(GenerationResult.Failed.class, r);
        assertEquals(5, fake.requests.size(), "1 call + maxRateLimitRetries (4)");
        assertTrue(joined(f.errors()).contains("rate"), "say it was rate limited: " + f.errors());
    }

    @Test
    void deadlineIsRespected() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.limited(Duration.ofSeconds(15)), FakeGemini.Step.limited(Duration.ofSeconds(15)),
                FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult.Failed f = assertInstanceOf(GenerationResult.Failed.class, run(fake, 3));
        Duration slept = time.sleeps.stream().reduce(Duration.ZERO, Duration::plus);
        assertTrue(slept.compareTo(Duration.ofSeconds(20)) <= 0, "slept " + slept + " past the 20 s deadline");
        assertTrue(joined(f.errors()).contains("deadline"), "say the deadline was hit: " + f.errors());
    }

    // ------------------------------------------------------------ cost

    @Test
    void usageIsSummedAcrossAttempts() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.limited(null), FakeGemini.Step.ok("oops"), FakeGemini.Step.ok(Fixtures.VALID3));
        GenerationResult r = run(fake, 3);
        assertInstanceOf(GenerationResult.Success.class, r);
        assertEquals(2400, r.usage().inputTokens(), "two answered calls x 1200 input tokens; the 429 costs nothing");
        assertEquals(1200, r.usage().outputTokens());
        assertEquals(2400 * 0.30 / 1e6 + 1200 * 2.50 / 1e6, r.usage().costUsd(), 1e-9);
    }
}
