"""Build the supervised tuning dataset for Gemini (JSONL, one conversation per line).

Format, per line (see "Prepare supervised tuning data" in the study plan):
  {"systemInstruction": {"role": "system", "parts": [{"text": SYSTEM}]},
   "contents": [{"role": "user",  "parts": [{"text": <prompt>}]},
                {"role": "model", "parts": [{"text": <the item as compact JSON>}]}]}
"""

from __future__ import annotations

SYSTEM = ("You write one multiple-choice quiz item for adult learners from the section text. Return JSON with "
          "stem, options (4), answerIndex, explanation and sectionId.")


def prompt_for(rec: dict) -> str:
    return f"Lesson {rec['lessonId']}, section {rec['item']['sectionId']}.\n\n{rec['sectionText']}\n\nWrite one quiz item."


def to_example(rec: dict) -> dict:
    """One authored record -> one tuning example. TODO(w6-c1)"""
    return {}


def normalize(stem: str) -> str:
    return " ".join(stem.lower().split())


def build_dataset(authored: list[dict], heldout: list[dict], val_percent: int = 10) -> tuple[list[dict], list[dict], dict]:
    """Return (train_examples, validation_examples, report).

    - drop duplicates: records whose normalized stem was already seen (keep the first by id order)
    - drop leakage: records whose normalized stem equals a held-out item's normalized stem
      (held-out records carry the stem in heldout[i]["stem"] if present, else are matched by section text)
    - split deterministically: validation if int(sha256(id).hexdigest(), 16) % 100 < val_percent
    - report: {"input": n, "duplicates": n, "leakage": n, "train": n, "validation": n}

    TODO(w6-c1)
    """
    return [], [], {}
