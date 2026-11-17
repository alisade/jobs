package com.kestrel.quizgen;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.junit.jupiter.api.Test;

class QuizGeneratorVisibleTest {

    @Test
    void parsesAValidResponse() {
        FakeGemini fake = new FakeGemini(FakeGemini.Step.ok(Fixtures.VALID3));
        FakeGemini.TestTime t = new FakeGemini.TestTime();
        GenerationResult r = new QuizGenerator(fake, QuizGenConfig.defaults(), t, t.clock(), () -> 0.5).generate(Fixtures.LESSON, 3);
        GenerationResult.Success ok = assertInstanceOf(GenerationResult.Success.class, r);
        assertEquals(3, ok.items().size());
        assertEquals("s3", ok.items().get(2).sectionId());
    }

    @Test
    void validatorRejectsThreeOptions() {
        QuizItem bad = new QuizItem("Which molecule forms the bilayer?", List.of("Phospholipid", "Glucose", "DNA"), 0, "s1", "s1");
        List<String> problems = new QuizValidator().validate(List.of(bad), Fixtures.LESSON, 1);
        assertFalse(problems.isEmpty(), "an item with 3 options must be rejected");
    }
}
