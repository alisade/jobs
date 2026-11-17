"""``python -m evals fixtures [--k 2]``: run the suite over recorded runs and print the
summary as JSON. Given."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .fake_judge import FakeJudgeClient
from .report import run_suite, summarize
from .transcript import load_transcripts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures", type=Path)
    ap.add_argument("--k", type=int, default=2)
    args = ap.parse_args()
    transcripts = load_transcripts(args.fixtures / "transcripts")
    judge = FakeJudgeClient.from_file(args.fixtures / "judge_verdicts.json")
    print(json.dumps(summarize(run_suite(transcripts, judge_client=judge), args.k), indent=2))


if __name__ == "__main__":
    main()
