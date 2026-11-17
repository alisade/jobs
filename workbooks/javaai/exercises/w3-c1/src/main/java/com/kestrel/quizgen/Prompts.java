package com.kestrel.quizgen;

import java.util.stream.Collectors;

/** Prompt text. The lesson goes in the user turn; the rules in the system instruction. */
public final class Prompts {
    private Prompts() { }

    public static final String SYSTEM = """
            You write multiple-choice quiz items for adult learners on Kestrel Learning.
            Use only the lesson text provided. Every item has exactly 4 options, one correct answer,
            plausible distractors, an explanation of why the answer is right, and the id of the
            section the explanation comes from. Never put the correct answer's wording in the stem.
            """;

    public static String userPrompt(Model.Lesson lesson, int count) {
        String sections = lesson.sections().stream()
                .map(s -> "[section " + s.id() + "] " + s.heading() + "\n" + s.text())
                .collect(Collectors.joining("\n\n"));
        return "Lesson: " + lesson.title() + "\n\n" + sections + "\n\nWrite " + count + " quiz items.";
    }
}
