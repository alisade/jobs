"""Tools the tutor may use. Backed by fixtures here; by the Spring Boot API in production."""

from __future__ import annotations

import json
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent.parent / "fixtures" / "data.json").read_text())
WRITES: list[dict] = []  # anything written by a write tool lands here (tests inspect it)


def search_course(course_id: str, query: str, k: int = 2) -> list[dict]:
    """Keyword search over a course's sections. Returns [{section_id, text}]."""
    course = DATA["courses"].get(course_id)
    if course is None:
        raise LookupError(f"unknown course {course_id}")
    words = {w.strip("?.,!").lower() for w in query.split() if len(w) > 2}
    scored = []
    for s in course["sections"]:
        text = s["text"].lower()
        score = sum(1 for w in words if w in text)
        if score:
            scored.append((score, s["id"], s["text"]))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [{"section_id": sid, "text": text} for _, sid, text in scored[:k]]


def get_learner_progress(learner_id: str, course_id: str) -> dict:
    """Read-only: mastered and in-progress lessons. Never returns quiz answers."""
    p = DATA["progress"].get(learner_id, {}).get(course_id)
    if p is None:
        return {"learner_id": learner_id, "course_id": course_id, "mastered": [], "in_progress": []}
    return {"learner_id": learner_id, "course_id": course_id, "mastered": p["mastered"], "in_progress": p["inProgress"]}


def record_mastery(learner_id: str, lesson_id: str) -> dict:
    """WRITE: marks a lesson mastered. Owned by the Spring Boot API; the tutor must never call it."""
    WRITES.append({"learner_id": learner_id, "lesson_id": lesson_id})
    return {"ok": True}


def current_quiz_answer(learner_id: str, course_id: str) -> str | None:
    """The correct answer of the quiz the learner is working on (for the leak guard only)."""
    p = DATA["progress"].get(learner_id, {}).get(course_id)
    if not p or not p["inProgress"]:
        return None
    return p.get("quizAnswer", {}).get(p["inProgress"][0])


def course_keywords(course_id: str) -> list[str]:
    course = DATA["courses"].get(course_id)
    return list(course["keywords"]) if course else []


REGISTRY = {
    "search_course": search_course,
    "get_learner_progress": get_learner_progress,
    "record_mastery": record_mastery,
}
