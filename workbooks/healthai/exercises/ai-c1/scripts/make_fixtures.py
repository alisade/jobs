"""Build the synthetic eval set, policy text and recorded runs (fixed seed). python scripts/make_fixtures.py"""

import copy
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "fixtures"
POLICY = {
    "KHP-MP-0417 2.a": "Lumbar MRI is covered when radicular pain persists for at least six weeks.",
    "KHP-MP-0417 2.b": "At least six weeks of conservative therapy such as physical therapy must be documented.",
    "KHP-MP-0417 2.c": "Red flag symptoms such as cauda equina syndrome waive the six week requirement.",
    "KHP-MP-0212 3.a": "Cardiac PET requires a prior nondiagnostic stress test within twelve months.",
    "KHP-MP-0212 3.b": "Body habitus or attenuation artifact limiting SPECT must be documented.",
    "KHP-MP-0388 1.a": "Knee arthroscopy requires mechanical symptoms and failed conservative management.",
    "KHP-MP-0388 1.b": "Imaging must show a meniscal tear consistent with the exam findings.",
}
CRIT = {"lumbar-mri": ["KHP-MP-0417 2.a", "KHP-MP-0417 2.b"], "cardiac-pet": ["KHP-MP-0212 3.a", "KHP-MP-0212 3.b"],
        "knee-arthroscopy": ["KHP-MP-0388 1.a", "KHP-MP-0388 1.b"]}


def quote(sec):
    words = POLICY[sec].split()
    return " ".join(words[2:8])


def main():
    rng = random.Random(57)
    cases, runs = [], {1: [], 2: [], 3: []}
    for i in range(1, 31):
        svc = rng.choice(sorted(CRIT))
        gold = {f"C{j + 1}": rng.random() < 0.75 for j in range(2)}
        cid = f"EV-{i:03d}"
        cases.append({"case_id": cid, "service": svc, "gold_criteria": gold,
                      "gold_route": "auto" if all(gold.values()) else "review"})
        for r in (1, 2, 3):
            met = dict(gold)
            if (i * r) % 23 == 0:
                met["C2"] = not met["C2"]  # a rare model mistake
            allmet = all(met.values())
            out = {"outcome": "approve" if allmet else rng.choice(["deny", "pend"]),
                   "confidence": round(rng.uniform(0.86, 0.97) if allmet else rng.uniform(0.5, 0.9), 2),
                   "route": "auto" if allmet else "review",
                   "criteria": [{"criterion_id": c, "met": met[c], "citation": CRIT[svc][j], "quote": quote(CRIT[svc][j])}
                                for j, c in enumerate(sorted(met))]}
            runs[r].append({"case_id": cid, "output": json.dumps(out), "latency_ms": rng.randint(900, 2600),
                            "input_tokens": rng.randint(2800, 4200), "output_tokens": rng.randint(180, 420)})
    (ROOT / "runs" / "good").mkdir(parents=True, exist_ok=True)
    json.dump(cases, open(ROOT / "cases.json", "w"), indent=1)
    json.dump(POLICY, open(ROOT / "policy.json", "w"), indent=1)
    for r, rows in runs.items():
        json.dump(rows, open(ROOT / "runs" / "good" / f"run{r}.json", "w"), indent=1)

    def variant(name, fn):
        d = ROOT / "runs" / name
        d.mkdir(parents=True, exist_ok=True)
        for r, rows in runs.items():
            rows = copy.deepcopy(rows)
            fn(r, rows)
            json.dump(rows, open(d / f"run{r}.json", "w"), indent=1)

    def schema(r, rows):
        if r == 2:
            rows[4]["output"] = "Approved. The member meets criteria."

    def citation(r, rows):
        for row in rows[:9]:
            o = json.loads(row["output"])
            o["criteria"][0]["quote"] = "the member clearly meets all requirements"
            row["output"] = json.dumps(o)

    def accuracy(r, rows):
        for row in rows[::3]:
            o = json.loads(row["output"])
            for c in o["criteria"]:
                c["met"] = not c["met"]
            row["output"] = json.dumps(o)

    def safety(r, rows):
        if r == 3:
            o = json.loads(rows[7]["output"])
            o.update(outcome="deny", route="auto", confidence=0.99)
            rows[7]["output"] = json.dumps(o)

    def variance(r, rows):
        if r == 2:
            for row in rows[:8]:
                o = json.loads(row["output"])
                o["outcome"] = {"approve": "pend", "deny": "approve", "pend": "deny"}[o["outcome"]]
                o["route"] = "review"
                row["output"] = json.dumps(o)

    for name, fn in (("regress_schema", schema), ("regress_citation", citation), ("regress_accuracy", accuracy),
                     ("regress_safety", safety), ("regress_variance", variance)):
        variant(name, fn)
    json.dump({"citation_support": 0.95, "criteria_accuracy": 0.93, "consistency": 0.95, "tolerance": 0.05,
               "price_per_mtok": {"input": 1.25, "output": 10.0}}, open(ROOT / "baseline.json", "w"), indent=1)


if __name__ == "__main__":
    main()
