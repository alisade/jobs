"""One assistant turn: tools, prompt, model, grounding check (local stand-in for the service)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from . import catalog, grounding, prompting

log = logging.getLogger("assistant")

FALLBACK = ("I could not verify prices or promotions for that just now. The product page always shows the "
            "current price, and a store associate can help with offers.")


class RecordedModel:
    """Replays the model outputs recorded in production for each question (data/recorded_outputs.json)."""

    def __init__(self, path: str | Path | None = None) -> None:
        path = path or Path(__file__).resolve().parent.parent / "data" / "recorded_outputs.json"
        self.outputs = json.loads(Path(path).read_text())
        self.prompts: list[str] = []

    def complete(self, question: str, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.outputs[question]["answer"]


def respond(question: str, skus: list[str], model) -> dict:
    records = catalog.search_products(skus)
    promos = catalog.active_promotions()
    prompt = prompting.build_prompt(question, records, promos)
    answer = model.complete(question, prompt)
    result = grounding.check(answer, records, promos)
    log.info("grounding grounded=%s problems=%s", result.grounded, result.problems)
    if not result.grounded:
        return {"answer": FALLBACK, "blocked": True, "problems": result.problems}
    return {"answer": answer, "blocked": False, "problems": []}
