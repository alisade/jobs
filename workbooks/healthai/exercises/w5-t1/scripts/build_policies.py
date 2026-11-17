"""Generate the synthetic KHP policy documents (markdown) and labelled queries (deterministic)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

TOPICS = [
    ("KHP-MP-0417", "Lumbar spine MRI", "lumbar", ["radiculopathy", "neurologic deficit", "cauda equina", "red flag symptoms", "prior surgery", "malignancy history"]),
    ("KHP-MP-0101", "Infliximab for inflammatory bowel disease", "infliximab", ["fistulizing disease", "steroid dependence", "mesalamine failure", "azathioprine trial", "tuberculosis screening", "hepatitis B screening"]),
    ("KHP-MP-0611", "Attended sleep study", "polysomnography", ["apnea hypopnea index", "home test failure", "hypoventilation", "neuromuscular disease", "epworth score", "cardiopulmonary comorbidity"]),
    ("KHP-MP-0903", "Outpatient physical therapy", "rehabilitation", ["functional goals", "progress notes", "visit limit", "plan of care", "maintenance therapy", "home exercise program"]),
    ("KHP-MP-0815", "Continuous glucose monitor", "glucose", ["insulin regimen", "hypoglycemia unawareness", "fingerstick frequency", "diabetes education", "endocrinology visit", "sensor adherence"]),
    ("KHP-MP-0520", "Bariatric surgery", "bariatric", ["body mass index", "supervised diet", "psychological evaluation", "nutrition counseling", "comorbid hypertension", "smoking cessation"]),
]
FILLER = ("the reviewer confirms the record shows this element with dates and the ordering clinician "
          "documents it in the clinical notes submitted with the request").split()


def row_text(rng, topic, item, idx):
    words = rng.sample(FILLER, 14)
    return f"| 2.{chr(97 + idx)} | {item} for {topic}: " + " ".join(words) + f" | step therapy {idx + 1} weeks |"


def main(out: str) -> None:
    rng = random.Random(417)
    root = Path(out)
    (root / "policies").mkdir(parents=True, exist_ok=True)
    (root / "fixtures").mkdir(parents=True, exist_ok=True)
    queries = []
    for pid, title, topic, items in TOPICS:
        lines = [f"# {pid} {title}", "", "## Overview", "",
                 f"This medical policy describes when Kestrel Health Plan covers {title.lower()} for members. "
                 "It applies to commercial, Medicare Advantage and Medicaid managed care lines unless a state "
                 "rule requires otherwise. Coverage requires prior authorization.", "",
                 "## Coverage criteria", "", "### Criteria table", "",
                 "| Criterion | Requirement | Step therapy |", "|---|---|---|"]
        for i, item in enumerate(items):
            lines.append(row_text(rng, topic, item, i))
            queries.append({"id": f"{pid}-2.{chr(97 + i)}", "kind": "row", "policy_id": pid,
                            "text": f"{topic} {item} step therapy weeks",
                            "must_contain": f"| 2.{chr(97 + i)} | {item} for {topic}:"})
        lines += ["", "### Documentation", "",
                  f"Submit clinical notes for {topic} covering the last six months, the results of prior "
                  "treatment, and an attestation from the ordering clinician. Missing documentation results "
                  "in a request for information, not a denial.", "",
                  "## Exclusions", "",
                  f"Requests for {topic} that are investigational, cosmetic or duplicate a study performed in "
                  "the last twelve months are not covered under this policy.", ""]
        queries.append({"id": f"{pid}-docs", "kind": "text", "policy_id": pid,
                        "text": f"{topic} documentation attestation six months",
                        "must_contain": "attestation from the ordering clinician"})
        queries.append({"id": f"{pid}-excl", "kind": "text", "policy_id": pid,
                        "text": f"{topic} investigational cosmetic duplicate",
                        "must_contain": "investigational, cosmetic or duplicate"})
        (root / "policies" / f"{pid}.md").write_text("\n".join(lines) + "\n")
    (root / "fixtures" / "queries.json").write_text(json.dumps(queries, indent=1) + "\n")
    print(f"{len(TOPICS)} policies, {len(queries)} queries")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
