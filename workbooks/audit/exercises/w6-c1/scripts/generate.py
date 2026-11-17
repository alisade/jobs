"""Regenerate data/ (deterministic). The committed files are the output; you do not need to run this."""

from __future__ import annotations

import json
import random
from pathlib import Path

ATTR = ["approval_before_deploy", "independent_approver", "linked_change", "tests_passed"]
OUT = Path(__file__).resolve().parents[1] / "data"


def overall(lab: dict) -> str:
    v = lab.values()
    return "exception" if "exception" in v else ("needs_review" if "not_evaluable" in v else "pass")


def labels() -> list[dict]:
    rng = random.Random(2026)
    rows = []
    special = {
        "S004": {"independent_approver": "exception"},
        "S009": {"approval_before_deploy": "exception"},
        "S013": {"approval_before_deploy": "exception", "independent_approver": "exception"},
        "S018": {"tests_passed": "exception"},
        "S022": {"linked_change": "exception"},
        "S027": {"independent_approver": "exception"},
        "S011": {"tests_passed": "not_evaluable"},
        "S025": {"independent_approver": "not_evaluable"},
    }
    reviewers = ["human:r.okafor", "human:s.lindqvist"]
    for i in range(1, 31):
        sid = f"S{i:03d}"
        lab = {a: "pass" for a in ATTR}
        lab.update(special.get(sid, {}))
        rows.append({"sample_id": sid, "change_id": f"CHG-10{4100 + 7 * i}", "labels": lab, "overall": overall(lab),
                     "labeled_by": reviewers[i % 2], "labeled_at": f"2026-10-{1 + i % 20:02d}T15:{rng.randint(0, 59):02d}:00Z",
                     "label_set": "cm03-golden-v1"})
    return rows


def runs(lab_rows: list[dict], variant: str) -> list[dict]:
    rng = random.Random(7 if variant == "v3" else 11)
    out = []
    # which (sample, run) pairs the agent gets wrong, and how
    if variant == "v3":
        flips = {("S027", 2): ("independent_approver", "pass"), ("S025", 1): ("independent_approver", "pass"),
                 ("S025", 4): ("independent_approver", "pass"), ("S011", 3): ("tests_passed", "pass"),
                 ("S006", 5): ("tests_passed", "not_evaluable"), ("S020", 2): ("linked_change", "not_evaluable")}
    else:  # prompt v4 candidate: shorter instruction, misses self-approval via e-mail alias
        flips = {(s, k): ("independent_approver", "pass") for s in ("S004", "S027") for k in range(1, 6)}
        flips.update({("S013", k): ("independent_approver", "pass") for k in (1, 3)})
        flips.update({("S025", k): ("independent_approver", "pass") for k in range(1, 6)})
    for row in lab_rows:
        for k in range(1, 6):
            if variant == "v3" and (row["sample_id"], k) == ("S017", 5):
                continue  # the run timed out and was never recorded
            o = dict(row["labels"])
            if (row["sample_id"], k) in flips:
                a, v = flips[(row["sample_id"], k)]
                o[a] = v
            prompt = rng.randint(2400, 3100) if variant == "v3" else rng.randint(1700, 2200)
            cached = 0 if k == 1 else (rng.randint(1700, 2000) if variant == "v3" else rng.randint(1200, 1500))
            out.append({"sample_id": row["sample_id"], "run": k, "prompt_version": variant, "model": "gemini-3.8-flash",
                        "outputs": o, "overall": overall(o),
                        "usage": {"prompt_tokens": prompt, "cached_tokens": cached, "output_tokens": rng.randint(110, 260)},
                        "latency_ms": rng.randint(1800, 4200) + (6000 if rng.random() < 0.06 else 0)})
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    lab = labels()
    (OUT / "labels.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in lab))
    (OUT / "runs.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in runs(lab, "v3")))
    (OUT / "runs_prompt_v4.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in runs(lab, "v4")))


if __name__ == "__main__":
    main()
