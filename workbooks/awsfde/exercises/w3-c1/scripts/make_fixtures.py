"""Regenerate fixtures/ (golden set and recorded Retrieve responses for two KB configs).

Deterministic. The recordings stand in for two Knowledge Bases over the same S3 prefix: one with
fixed-size chunking (300 tokens, 20% overlap) and one with hierarchical chunking (parent 1500 /
child 300). Run: python scripts/make_fixtures.py
"""

from __future__ import annotations

import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUCKET = "s3://tidewater-kb-docs-111122223333/tenants"
TOPICS = ["returns-policy", "cold-chain-sop", "carrier-sla", "invoice-disputes", "onboarding-guide",
          "customs-holds", "damage-claims", "pallet-specs", "holiday-cutoffs", "api-limits"]
TENANTS = ["acme-foods", "brightline-health", "corvid-logistics"]


def uri(tenant: str, topic: str, part: int = 1) -> str:
    return f"{BUCKET}/{tenant}/docs/{topic}-{part}.pdf"


def main() -> None:
    rng = random.Random(20261113)
    golden = []
    qn = 0
    for tenant in TENANTS:
        for topic in rng.sample(TOPICS, 7 if tenant != "corvid-logistics" else 6):
            qn += 1
            exp = [uri(tenant, topic, 1)] + ([uri(tenant, topic, 2)] if rng.random() < 0.3 else [])
            golden.append({"id": f"q{qn:02d}", "tenant_id": tenant,
                           "question": f"[{tenant}] What does our {topic.replace('-', ' ')} document say about exceptions?",
                           "expected_uris": exp})

    def results(q: dict, quality: float, leak: bool) -> list[dict]:
        out = []
        noise = [uri(q["tenant_id"], t, 1) for t in TOPICS if uri(q["tenant_id"], t, 1) not in q["expected_uris"]]
        rng.shuffle(noise)
        hits = list(q["expected_uris"])
        ranked: list[str] = []
        for h in hits:
            if rng.random() < quality:
                ranked.insert(rng.randint(0, min(2, len(ranked))), h)
        ranked += noise[: 6 - len(ranked)]
        if rng.random() > quality and q["expected_uris"][0] not in ranked:
            ranked.insert(4, q["expected_uris"][0])
        # chunk-level duplicates: the same document often returns two chunks
        if ranked:
            ranked.insert(1, ranked[0])
        for i, u in enumerate(ranked[:7]):
            tenant = u.split("/tenants/")[1].split("/")[0]
            out.append({
                "content": {"text": f"chunk {i} of {u.rsplit('/', 1)[1]}", "type": "TEXT"},
                "location": {"type": "S3", "s3Location": {"uri": u}},
                "metadata": {"tenant_id": tenant, "x-amz-bedrock-kb-source-uri": u},
                "score": round(0.92 - i * 0.07 + rng.random() * 0.01, 4),
            })
        if leak:
            other = "acme-foods" if q["tenant_id"] != "acme-foods" else "corvid-logistics"
            u = uri(other, "carrier-sla", 1)
            out.insert(2, {"content": {"text": "chunk from another tenant", "type": "TEXT"},
                           "location": {"type": "S3", "s3Location": {"uri": u}},
                           "metadata": {"tenant_id": other, "x-amz-bedrock-kb-source-uri": u}, "score": 0.81})
        return out[:5] if len(out) > 5 else out

    rec = {}
    for cfg, quality in (("fixed", 0.72), ("hierarchical", 0.93)):
        rec[cfg] = {q["id"]: results(q, quality, leak=(cfg == "fixed" and q["id"] == "q09")) for q in golden}
    (ROOT / "fixtures").mkdir(exist_ok=True)
    (ROOT / "fixtures" / "golden.json").write_text(json.dumps(golden, indent=1) + "\n")
    for cfg, r in rec.items():
        (ROOT / "fixtures" / f"recorded-{cfg}.json").write_text(json.dumps(r, indent=1) + "\n")
    print(f"{len(golden)} golden questions; recordings: {', '.join(rec)}")


if __name__ == "__main__":
    main()
