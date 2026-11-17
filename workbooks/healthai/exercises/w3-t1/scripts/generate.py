"""Synthetic intake records for the incident window (fixed seed). python scripts/generate.py data"""

import json
import random
import sys
from pathlib import Path

DX = {"oncology-pet": ["C3490", "C509", "C189"], "chemo-infusion": ["C509", "D0510", "C61"],
      "cardiac-pet": ["I2510", "I209", "I5023"], "cardiac-cath": ["I2111", "R079", "I2510"],
      "lumbar-mri": ["M5416", "M5126"], "knee-arthroscopy": ["M23221", "M1711"]}


def main(out):
    rng = random.Random(278)
    recs = []
    for i in range(1, 121):
        svc = rng.choice(list(DX))
        dx = rng.sample(DX[svc], k=rng.choice([1, 1, 2]))
        if rng.random() < 0.05:
            dx = []
        recs.append({"case_id": f"PA-2026-{80000 + i}", "member_id": f"M-{100200 + rng.randrange(1, 90)}",
                     "service": svc, "diagnoses": dx})
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / "requests.json").write_text(json.dumps(recs, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
