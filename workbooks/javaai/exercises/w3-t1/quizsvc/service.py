"""Quiz generation service (release 2.3). Called by the Spring Boot API's /quiz/generate."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import yaml

from .gemini import RateLimited

log = logging.getLogger("quizsvc")
ROOT = Path(__file__).resolve().parent.parent
MODEL = "gemini-2.5-flash"


def load_safety_settings(path: Path = ROOT / "config" / "safety.yaml") -> list[dict]:
    cfg = yaml.safe_load(path.read_text())
    return [{"category": c, "threshold": t} for c, t in cfg["thresholds"].items()]


def load_lesson(lesson_id: str) -> dict:
    lessons = json.loads((ROOT / "fixtures" / "lessons.json").read_text())
    if lesson_id not in lessons:
        raise KeyError(lesson_id)
    return lessons[lesson_id]


def build_request(lesson: dict, count: int) -> dict:
    sections = "\n\n".join(f"[section {s['id']}] {s['heading']}\n{s['text']}" for s in lesson["sections"])
    return {
        "model": MODEL,
        "labels": {"lesson_id": lesson["id"], "feature": "quiz-generate"},
        "systemInstruction": {"parts": [{"text": "You write multiple-choice quiz items for adult university learners."}]},
        "contents": [{"role": "user", "parts": [{"text": f"Lesson: {lesson['title']}\n\n{sections}\n\nWrite {count} items."}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        "safetySettings": load_safety_settings(),
    }


def call_with_retry(client, request: dict, attempts: int = 3, base: float = 0.05) -> dict:
    for i in range(attempts):
        try:
            return client.generate_content(request)
        except RateLimited as e:
            log.warning("gemini 429 lesson=%s attempt=%d: %s", request["labels"]["lesson_id"], i + 1, e)
            if i == attempts - 1:
                raise
            time.sleep(base * (2 ** i))
    raise AssertionError("unreachable")


def generate_quiz(client, lesson_id: str, count: int = 3) -> dict:
    lesson = load_lesson(lesson_id)
    resp = call_with_retry(client, build_request(lesson, count))
    text = resp["candidates"][0]["content"]["parts"][0]["text"]
    items = json.loads(text)["items"]
    usage = resp.get("usageMetadata", {})
    log.info("quiz generated lesson=%s items=%d tokens=%s", lesson_id, len(items), usage.get("totalTokenCount"))
    return {"status": "ok", "lessonId": lesson_id, "items": items, "usage": usage}
