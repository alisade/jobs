"""Replay every recorded production question through the pipeline and show what customers would see."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.pipeline import RecordedModel, respond  # noqa: E402


def main() -> None:
    model = RecordedModel()
    for q, rec in model.outputs.items():
        out = respond(q, rec["skus"], model)
        flag = "BLOCKED" if out["blocked"] else "SHOWN  "
        print(f"{flag} {rec['conversation_id']}  Q: {q}")
        print(f"        A: {out['answer']}")
        for p in out["problems"]:
            print(f"        - {p}")
    if "--prompt" in sys.argv:
        print("\n--- prompt the model saw for the first question ---")
        print(model.prompts[0])


if __name__ == "__main__":
    main()
