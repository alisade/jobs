"""Build the supervised tuning dataset for Gemini (JSONL, one conversation per line).

Format, per line (see "Prepare supervised tuning data" in the study plan):
  {"systemInstruction": {"role": "system", "parts": [{"text": SYSTEM}]},
   "contents": [{"role": "user",  "parts": [{"text": <prompt>}]},
                {"role": "model", "parts": [{"text": <the item as compact JSON>}]}]}
"""

from __future__ import annotations

import hashlib
import json

SYSTEM = ("You write one multiple-choice quiz item for adult learners from the section text. Return JSON with "
          "stem, options (4), answerIndex, explanation and sectionId.")


def prompt_for(rec: dict) -> str:
    return f"Lesson {rec['lessonId']}, section {rec['item']['sectionId']}.\n\n{rec['sectionText']}\n\nWrite one quiz item."


def to_example(rec: dict) -> dict:
    """One authored record -> one tuning example."""
    return {
        "systemInstruction": {"role": "system", "parts": [{"text": SYSTEM}]},
        "contents": [
            {"role": "user", "parts": [{"text": prompt_for(rec)}]},
            {"role": "model", "parts": [{"text": json.dumps(rec["item"], separators=(",", ":"))}]},
        ],
    }


def normalize(stem: str) -> str:
    return " ".join(stem.lower().split())


def build_dataset(authored: list[dict], heldout: list[dict], val_percent: int = 10) -> tuple[list[dict], list[dict], dict]:
    """Return (train_examples, validation_examples, report).

    - drop duplicates: records whose normalized stem was already seen (keep the first by id order)
    - drop leakage: records whose normalized stem equals a held-out item's normalized stem
      (held-out records carry the stem in heldout[i]["stem"] if present, else are matched by section text)
    - split deterministically: validation if int(sha256(id).hexdigest(), 16) % 100 < val_percent
    - report: {"input": n, "duplicates": n, "leakage": n, "train": n, "validation": n}

    """
    held_stems = {normalize(h["stem"]) for h in heldout if "stem" in h}
    held_texts = {h["sectionText"] for h in heldout}
    seen: set[str] = set()
    report = {"input": len(authored), "duplicates": 0, "leakage": 0, "train": 0, "validation": 0}
    train, val = [], []
    for rec in sorted(authored, key=lambda r: r["id"]):
        stem = normalize(rec["item"]["stem"])
        if stem in held_stems or rec["sectionText"] in held_texts:
            report["leakage"] += 1
            continue
        if stem in seen:
            report["duplicates"] += 1
            continue
        seen.add(stem)
        bucket = int(hashlib.sha256(rec["id"].encode()).hexdigest(), 16) % 100
        (val if bucket < val_percent else train).append(to_example(rec))
    report["train"], report["validation"] = len(train), len(val)
    return train, val, report
