package com.kestrel.quizgen;

import java.util.List;

/** One generated multiple-choice item. sectionId cites the lesson section the explanation is grounded in. */
public record QuizItem(String stem, List<String> options, int answerIndex, String explanation, String sectionId) { }
