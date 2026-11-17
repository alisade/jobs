package com.kestrel.quizgen;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;

/** Checks what a schema cannot: counts, ranges, uniqueness, grounding and giveaways. */
public final class QuizValidator {

    private static String norm(String s) { return s == null ? "" : s.trim().toLowerCase(Locale.ROOT); }

    public List<String> validate(List<QuizItem> items, Model.Lesson lesson, int expectedCount) {
        List<String> problems = new ArrayList<>();
        if (items == null) {
            problems.add("expected " + expectedCount + " items, got none");
            return problems;
        }
        if (items.size() != expectedCount) problems.add("expected " + expectedCount + " items, got " + items.size());
        Set<String> sections = lesson.sections().stream().map(Model.Section::id).collect(Collectors.toSet());
        Set<String> stems = new HashSet<>();
        for (int i = 0; i < items.size(); i++) {
            QuizItem q = items.get(i);
            String p = "item " + (i + 1) + ": ";
            if (q == null) { problems.add(p + "is null"); continue; }
            if (norm(q.stem()).isEmpty()) problems.add(p + "stem is blank");
            else if (!stems.add(norm(q.stem()))) problems.add(p + "duplicate stem of an earlier item");
            if (norm(q.explanation()).isEmpty()) problems.add(p + "explanation is blank");
            if (q.sectionId() == null || !sections.contains(q.sectionId()))
                problems.add(p + "sectionId '" + q.sectionId() + "' is not a section of this lesson " + sections);
            List<String> opts = q.options();
            if (opts == null || opts.size() != 4) {
                problems.add(p + "options must have exactly 4 entries, got " + (opts == null ? 0 : opts.size()));
            } else {
                Set<String> seen = new HashSet<>();
                for (String o : opts) {
                    if (norm(o).isEmpty()) problems.add(p + "options contain a blank entry");
                    else if (!seen.add(norm(o))) problems.add(p + "duplicate option '" + o.trim() + "'");
                }
            }
            int n = (opts == null || opts.isEmpty()) ? 4 : opts.size();
            if (q.answerIndex() < 0 || q.answerIndex() >= n) {
                problems.add(p + "answerIndex " + q.answerIndex() + " is out of range 0-" + (n - 1));
            } else if (opts != null && q.answerIndex() < opts.size()) {
                String answer = norm(opts.get(q.answerIndex()));
                if (answer.length() >= 4 && norm(q.stem()).contains(answer))
                    problems.add(p + "stem reveals the answer ('" + opts.get(q.answerIndex()).trim() + "')");
            }
        }
        return problems;
    }
}
