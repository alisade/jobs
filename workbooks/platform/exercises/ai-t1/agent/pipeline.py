"""One agent run: plan, let the model summarize, verify, open the PR."""

from __future__ import annotations

from pathlib import Path

from . import tools, verify
from .llm import FakeModel
from .prompt import SYSTEM


def run(plan_json_path: str | Path, model=None, outbox: list | None = None) -> dict:
    model = model or FakeModel()
    outbox = outbox if outbox is not None else []
    tool_out = tools.terraform_plan(plan_json_path)
    claim = model.summarize(SYSTEM, tool_out)
    verdict = verify.verify(plan_json_path, claim)
    pr = None
    if verdict.ok:
        c = verdict.counts
        pr = {"title": "import: unmanaged resources",
              "body": f"plan: {c['import']} to import, {c['change']} to change, {c['destroy']} to destroy"}
        outbox.append(pr)
    return {"pr_opened": pr is not None, "pr": pr, "verdict": verdict, "claim": claim}


if __name__ == "__main__":
    import sys
    res = run(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "evidence" / "plan-run-212.json")
    print("model claim:", res["claim"])
    print("verdict:", res["verdict"])
    print("PR opened:", res["pr_opened"], "-", res["pr"]["body"] if res["pr"] else "")
