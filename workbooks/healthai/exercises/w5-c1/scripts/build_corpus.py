"""Build the synthetic KHP medical-policy corpus and the labelled query set (deterministic).

python scripts/build_corpus.py fixtures
The fixtures are committed; this script documents how they were made.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

POLICIES = [
    # id, title, topic doc words, topic query synonyms, exact tokens, lobs
    ("KHP-MP-0417", "Lumbar spine MRI", "lumbar spine mri", "lower back scan", "radiculopathy", ["commercial", "medicare-advantage", "medicaid-mco"]),
    ("KHP-MP-0212", "Knee arthroscopy", "knee arthroscopy meniscus", "joint keyhole cartilage", "M23.221", ["commercial", "medicare-advantage"]),
    ("KHP-MP-0388", "Cardiac PET perfusion", "cardiac pet perfusion", "heart nuclear bloodflow", "I25.10", ["medicare-advantage", "medicaid-mco"]),
    ("KHP-MP-0101", "Infliximab infusion for inflammatory bowel disease", "infliximab bowel crohn", "biologic gut colitis", "J1745", ["commercial", "medicaid-mco"]),
    ("KHP-MP-0520", "Bariatric surgery", "bariatric surgery obesity", "weightloss operation overweight", "E66.01", ["commercial"]),
    ("KHP-MP-0611", "Attended sleep study", "polysomnography sleep apnea", "overnight snoring breathing", "G47.33", ["commercial", "medicare-advantage", "medicaid-mco"]),
    ("KHP-MP-0702", "Home infusion therapy", "home infusion antibiotic", "residence drip antimicrobial", "S9500", ["medicare-advantage", "medicaid-mco"]),
    ("KHP-MP-0815", "Continuous glucose monitor", "glucose monitor diabetes", "sugar sensor diabetic", "E2103", ["commercial", "medicaid-mco"]),
    ("KHP-MP-0903", "Outpatient physical therapy", "physical therapy rehabilitation", "physio exercises recovery", "G0283", ["commercial", "medicare-advantage", "medicaid-mco"]),
    ("KHP-MP-0950", "Hereditary cancer genetic testing", "genetic testing brca", "hereditary gene mutation", "Z80.3", ["commercial", "medicare-advantage"]),
]

SECTIONS = [
    # key, heading, doc words, query synonyms
    ("criteria", "Coverage criteria", "coverage criteria medically necessary", "qualify eligible requirements"),
    ("step", "Step therapy", "step therapy conservative trial", "firstline before tried"),
    ("docs", "Documentation required", "documentation records attestation", "paperwork submit notes"),
    ("exclusions", "Exclusions", "exclusions investigational cosmetic", "excluded experimental notcovered"),
    ("codes", "Codes", "codes hcpcs icd-10-cm", "billing codeset coding"),
    ("reauth", "Reauthorization", "reauthorization renewal continuation", "renew extend repeat"),
]

RETIRED = {"KHP-MP-0417", "KHP-MP-0101", "KHP-MP-0611", "KHP-MP-0903"}


def concept_table() -> dict[str, str]:
    """word -> concept id, for the stub embedding. Doc words and query synonyms share a concept."""
    table: dict[str, str] = {}
    for pid, _t, doc, syn, _e, _l in POLICIES:
        for i, (d, s) in enumerate(zip(doc.split(), syn.split())):
            table[d] = table[s] = f"{pid}:{i}"
    for key, _h, doc, syn in SECTIONS:
        for i, (d, s) in enumerate(zip(doc.split(), syn.split())):
            table[d] = table[s] = f"sec:{key}:{i}"
    return table


def main(out: str) -> None:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = []
    for pid, title, topic, _syn, exact, lobs in POLICIES:
        versions = [("v3", "2026-01-01", None, False)]
        if pid in RETIRED:
            versions.append(("v2", "2024-07-01", "2026-01-01", True))
        for ver, start, end, retired in versions:
            for key, heading, words, _q in SECTIONS:
                text = f"Policy {pid} {title}. {heading}. {topic} {words}."
                if key in ("codes", "criteria"):
                    text += f" {exact}."
                if retired:
                    text += " Prior version retained for appeals lookups."
                docs.append({
                    "id": f"{pid}-{ver}-{key}", "policy_id": pid, "version": ver, "section": key,
                    "section_path": f"{pid} > {heading}", "text": text, "lobs": lobs,
                    "effective_from": start, "effective_to": end,
                })
    queries = []
    n = 0
    for pid, _t, _topic, syn, exact, lobs in POLICIES:
        for key, _h, words, qsyn in SECTIONS:
            gold = f"{pid}-v3-{key}"
            lob = lobs[n % len(lobs)]
            n += 1
            queries.append({"id": f"Q{n:03d}", "kind": "exact", "text": f"{pid} {words.split()[0]}",
                            "lob": lob, "as_of": "2026-11-01", "gold": gold})
            if key in ("step", "criteria", "reauth", "exclusions"):
                n += 1
                queries.append({"id": f"Q{n:03d}", "kind": "paraphrase", "text": f"{syn} {qsyn}",
                                "lob": lob, "as_of": "2026-11-01", "gold": gold})
    (out_dir / "corpus.json").write_text(json.dumps(docs, indent=1) + "\n")
    (out_dir / "queries.json").write_text(json.dumps(queries, indent=1) + "\n")
    (out_dir / "concepts.json").write_text(json.dumps(concept_table(), indent=1, sort_keys=True) + "\n")
    print(f"{len(docs)} sections, {len(queries)} queries")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fixtures")
