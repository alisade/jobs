#!/usr/bin/env python3
"""Record a graded attempt and regenerate grades/grades.js for the HTML workbooks.

grades/grades.json is the source of truth. grades/grades.js is a generated copy
(window.GRADES = {...}) because file:// pages can load a <script src> but cannot
fetch() a local JSON file.

Usage:
  tools/update_grades.py record --id fde/w1-c1 --score 82 --tests-passed 7 \
      --tests-total 9 --summary "One line" --feedback grades/feedback/fde/w1-c1/<ts>.md
  tools/update_grades.py status            # table of every graded exercise
  tools/update_grades.py rebuild           # regenerate grades.js from grades.json
"""

import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "grades" / "grades.json"
JS_PATH = ROOT / "grades" / "grades.js"
PASS_MARK = 70


def load() -> dict:
    if not JSON_PATH.exists():
        return {}
    return json.loads(JSON_PATH.read_text() or "{}")


def save(data: dict) -> None:
    JSON_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    JS_PATH.write_text("window.GRADES = " + json.dumps(data, sort_keys=True) + ";\n")


def record(args: argparse.Namespace) -> None:
    if "/" not in args.id:
        sys.exit("--id must look like <track>/<exercise>, e.g. fde/w1-c1")
    if not 0 <= args.score <= 100:
        sys.exit("--score must be 0-100")
    data = load()
    entry = data.setdefault(args.id, {"attempts": []})
    attempt = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "score": args.score,
        "passed": args.score >= PASS_MARK,
        "tests_passed": args.tests_passed,
        "tests_total": args.tests_total,
        "summary": args.summary,
        "feedback": args.feedback,
    }
    entry["attempts"].append(attempt)
    entry["latest"] = args.score
    entry["best"] = max(a["score"] for a in entry["attempts"])
    save(data)
    print(f"recorded {args.id}: {args.score}/100 (best {entry['best']}, attempt {len(entry['attempts'])})")


def status(_: argparse.Namespace) -> None:
    data = load()
    if not data:
        print("no graded exercises yet")
        return
    print(f"{'exercise':<16} {'latest':>6} {'best':>5} {'tries':>5}  summary")
    for ex_id in sorted(data):
        e = data[ex_id]
        last = e["attempts"][-1]
        print(f"{ex_id:<16} {e['latest']:>6} {e['best']:>5} {len(e['attempts']):>5}  {last['summary'][:70]}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--id", required=True)
    r.add_argument("--score", type=int, required=True)
    r.add_argument("--tests-passed", type=int, default=0)
    r.add_argument("--tests-total", type=int, default=0)
    r.add_argument("--summary", required=True)
    r.add_argument("--feedback", required=True, help="path relative to the workbooks root")
    r.set_defaults(fn=record)
    sub.add_parser("status").set_defaults(fn=status)
    sub.add_parser("rebuild").set_defaults(fn=lambda _: save(load()))
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
