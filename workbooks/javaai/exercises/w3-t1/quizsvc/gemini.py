"""Replay stand-in for Gemini generateContent on Vertex AI (Gemini Enterprise Agent Platform).

Responses were recorded from the real service with every safety filter off, together with the
per-category safety ratings Gemini assigned to the prompt and to the answer. Replaying applies the
thresholds in the request's ``safetySettings`` the way the service does:

- a prompt rating at or above its threshold: no candidates, ``promptFeedback.blockReason = SAFETY``
- an answer rating at or above its threshold: one candidate with ``finishReason = SAFETY``,
  ``safetyRatings`` (the offending one has ``blocked: true``) and no ``content``
- otherwise: one candidate with ``content.parts[0].text`` and ``finishReason = STOP``

Do not change this file: it plays the role of the managed service.
"""

from __future__ import annotations

import json
from pathlib import Path

ORDER = ["NEGLIGIBLE", "LOW", "MEDIUM", "HIGH"]
# threshold -> lowest probability that is blocked
BLOCKS_FROM = {
    "BLOCK_LOW_AND_ABOVE": "LOW",
    "BLOCK_MEDIUM_AND_ABOVE": "MEDIUM",
    "BLOCK_ONLY_HIGH": "HIGH",
    "BLOCK_NONE": None,
    "OFF": None,
}
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "recorded.json"


class RateLimited(Exception):
    """HTTP 429 RESOURCE_EXHAUSTED."""


class ReplayGemini:
    def __init__(self, fixtures: Path = FIXTURES):
        self.recorded = json.loads(Path(fixtures).read_text())
        self.calls: list[dict] = []
        self._limited: dict[str, int] = {}

    def generate_content(self, request: dict) -> dict:
        self.calls.append(request)
        lesson_id = request["labels"]["lesson_id"]
        rec = self.recorded[lesson_id]
        n = self._limited.get(lesson_id, 0)
        if n < rec.get("rateLimitFirst", 0):
            self._limited[lesson_id] = n + 1
            raise RateLimited("429 RESOURCE_EXHAUSTED: Quota exceeded for aiplatform.googleapis.com/generate_content_requests_per_minute")
        thresholds = {s["category"]: s["threshold"] for s in request.get("safetySettings", [])}
        usage = rec["usage"]
        prompt_hit = self._hit(rec["promptRatings"], thresholds)
        if prompt_hit:
            return {"promptFeedback": {"blockReason": "SAFETY", "safetyRatings": self._ratings(rec["promptRatings"], prompt_hit)},
                    "usageMetadata": {"promptTokenCount": usage["promptTokenCount"], "totalTokenCount": usage["promptTokenCount"]},
                    "modelVersion": request["model"]}
        resp_hit = self._hit(rec["responseRatings"], thresholds)
        if resp_hit:
            return {"candidates": [{"finishReason": "SAFETY", "safetyRatings": self._ratings(rec["responseRatings"], resp_hit)}],
                    "usageMetadata": usage, "modelVersion": request["model"]}
        return {"candidates": [{"content": {"role": "model", "parts": [{"text": rec["text"]}]}, "finishReason": "STOP",
                                "safetyRatings": self._ratings(rec["responseRatings"], None)}],
                "usageMetadata": usage, "modelVersion": request["model"]}

    @staticmethod
    def _hit(ratings: dict, thresholds: dict) -> str | None:
        for cat, prob in ratings.items():
            start = BLOCKS_FROM.get(thresholds.get(cat, "BLOCK_MEDIUM_AND_ABOVE"))
            if start is not None and ORDER.index(prob) >= ORDER.index(start):
                return cat
        return None

    @staticmethod
    def _ratings(ratings: dict, blocked_cat: str | None) -> list[dict]:
        out = []
        for cat, prob in ratings.items():
            r = {"category": cat, "probability": prob}
            if cat == blocked_cat:
                r["blocked"] = True
            out.append(r)
        return out
