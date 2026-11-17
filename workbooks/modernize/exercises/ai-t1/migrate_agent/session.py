"""Replay a recorded 8-turn agent session through build_request and the fake API, and print usage per
turn. This is what the CI job does, minus the real model."""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta

from .fake_api import FakeMessagesApi
from .prompt import build_request, load_skills

REPO = [f"src/main/java/com/corvane/claimdesk/rating/{n}.java" for n in
        ["RatingEngine", "RatingExporter", "RatingResult", "Encodings", "Main", "Halberd", "Envelope", "Batch"]]
REPO += ["pom.xml", "src/test/java/com/corvane/claimdesk/rating/RatingExporterTest.java"]


def replay(seed: int = 1, turns: int = 8, start: datetime | None = None, shuffle_listing: bool = True) -> list[dict]:
    rnd = random.Random(seed)
    api = FakeMessagesApi()
    now = start or datetime(2026, 11, 12, 2, 0, 0)
    history: list[dict] = []
    skills = load_skills()
    rows = []
    files = list(REPO)
    if shuffle_listing:
        rnd.shuffle(files)   # the listing comes from a set in the CI job: order varies per process, not per turn
    for turn in range(1, turns + 1):
        req = build_request("Replace sun.misc.BASE64Encoder in claimdesk-rating.", files, skills, now, history)
        u = api.usage(req, now)
        rows.append({"turn": turn, **u, "cost_usd": round(FakeMessagesApi.cost(u), 5)})
        history += [{"role": "assistant", "content": f"(turn {turn} tool call)"},
                    {"role": "user", "content": f"(turn {turn} tool result)"}]
        now += timedelta(seconds=rnd.randint(4, 40))
    return rows


def main() -> int:
    rows = replay()
    print(f"{'turn':>4} {'input':>7} {'cache_write':>11} {'cache_read':>10} {'cost_usd':>9}")
    for r in rows:
        print(f"{r['turn']:>4} {r['input_tokens']:>7} {r['cache_creation_input_tokens']:>11} {r['cache_read_input_tokens']:>10} {r['cost_usd']:>9.5f}")
    print(f"total cost_usd {sum(r['cost_usd'] for r in rows):.5f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
