package com.kestrel.quizgen;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/** Scripted stand-in for Gemini on Vertex AI, plus a fake clock and sleeper that advance together. */
public final class FakeGemini implements Model.GeminiClient {

    /** One scripted step: a response, or a 429 (retryAfter may be null). */
    public record Step(Model.Response response, boolean rateLimited, Duration retryAfter) {
        public static Step ok(String text) { return new Step(new Model.Response(text, Model.FinishReason.STOP, 1200, 600), false, null); }
        public static Step finish(String text, Model.FinishReason reason) { return new Step(new Model.Response(text, reason, 1200, 300), false, null); }
        public static Step limited(Duration retryAfter) { return new Step(null, true, retryAfter); }
    }

    public final List<Model.Request> requests = new ArrayList<>();
    private final Deque<Step> script = new ArrayDeque<>();
    private Step last;

    public FakeGemini(Step... steps) { for (Step s : steps) script.add(s); }

    @Override
    public Model.Response generate(Model.Request request) throws Model.RateLimitedException {
        requests.add(request);
        Step s = script.isEmpty() ? last : script.poll();
        if (s == null) throw new IllegalStateException("script exhausted");
        last = s;
        if (s.rateLimited()) throw new Model.RateLimitedException(s.retryAfter());
        return s.response();
    }

    /** A clock you can move, and a sleeper that moves it. */
    public static final class TestTime implements Model.Sleeper {
        public Instant now = Instant.parse("2026-11-02T09:00:00Z");
        public final List<Duration> sleeps = new ArrayList<>();
        public Clock clock() {
            return new Clock() {
                @Override public ZoneOffset getZone() { return ZoneOffset.UTC; }
                @Override public Clock withZone(java.time.ZoneId zone) { return this; }
                @Override public Instant instant() { return now; }
            };
        }
        @Override public void sleep(Duration d) { sleeps.add(d); now = now.plus(d); }
    }
}
