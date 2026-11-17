package com.kestrel.quizgen;

import java.util.ArrayList;
import java.util.List;

/**
 * Checks what a schema cannot: counts, ranges, uniqueness, grounding and giveaways.
 * Returns human-readable problems; an empty list means valid. The messages are fed back to the
 * model on a corrective retry, so make them specific ("item 2: answerIndex 4 is out of range 0-3").
 */
public final class QuizValidator {

    public List<String> validate(List<QuizItem> items, Model.Lesson lesson, int expectedCount) {
        List<String> problems = new ArrayList<>();
        // TODO(w3-c1): implement every rule in README "Validation rules".
        return problems;
    }
}
