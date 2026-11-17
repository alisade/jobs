"""Knowledge base, metrics and mail relay stand-ins."""

from __future__ import annotations

import json
import pathlib

DOCS = pathlib.Path(__file__).resolve().parent / "docs"


class KnowledgeBase:
    """Returns the tenant's documents ingested on or before the run date, best match first."""

    def __init__(self, run_date: str) -> None:
        self.run_date = run_date
        self.manifest = json.loads((DOCS / "manifest.json").read_text())

    def search(self, tenant_id: str, query: str) -> list[dict]:
        words = set(query.lower().split())
        out = []
        for m in self.manifest:
            if m["tenant_id"] != tenant_id or m["ingested"] > self.run_date:
                continue
            text = (DOCS / m["file"]).read_text().strip()
            score = len(words & set(text.lower().replace(".", " ").split())) / max(1, len(words))
            out.append({"doc_id": m["doc_id"], "text": text, "score": round(score, 3), "uploaded_by": m["uploaded_by"]})
        return sorted(out, key=lambda d: (-d["score"], d["doc_id"]))[:3]


METRICS = {
    "corvid-logistics": {"on_time_pct": {"Rivermark Freight": 96.4, "Lakeshore Haulers": 91.2, "Northgate Carriers": 97.8},
                         "damage_claims": 4, "detention_hours": 63, "late_lanes": ["Toledo-Columbus", "Erie-Pittsburgh", "Buffalo-Chicago"]},
    "acme-foods": {"on_time_pct": {"ColdRoute": 95.0}, "damage_claims": 1, "detention_hours": 12, "late_lanes": ["Fresno-Boise"]},
}


class MailRelay:
    """The outbound relay. Everything handed to send() leaves the company."""

    def __init__(self) -> None:
        self.outbox: list[dict] = []

    def send(self, tenant_id: str, to: list[str], subject: str, body: str) -> str:
        msg_id = f"msg-{len(self.outbox) + 1:04d}"
        self.outbox.append({"message_id": msg_id, "tenant_id": tenant_id, "to": list(to), "subject": subject,
                            "body_chars": len(body)})
        return msg_id
