"""Regenerate evidence/ (the fake blob container's contents). The committed files are the output."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "evidence"


def para(content, page, role=None):
    p = {"content": content, "boundingRegions": [{"pageNumber": page, "polygon": [1.0, 1.0, 7.5, 1.0, 7.5, 1.3, 1.0, 1.3]}],
         "spans": [{"offset": 0, "length": len(content)}]}
    if role:
        p["role"] = role
    return p


def table(page, rows, header=True):
    cells = []
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = {"rowIndex": r, "columnIndex": c, "content": val, "boundingRegions": [{"pageNumber": page}]}
            if header and r == 0:
                cell["kind"] = "columnHeader"
            cells.append(cell)
    return {"rowCount": len(rows), "columnCount": len(rows[0]), "cells": cells, "boundingRegions": [{"pageNumber": page}]}


def layout(pages, paragraphs, tables=()):
    return {"apiVersion": "2024-11-30", "modelId": "prebuilt-layout", "content": "\n".join(p["content"] for p in paragraphs),
            "pages": [{"pageNumber": n, "width": 8.5, "height": 11, "unit": "inch"} for n in range(1, pages + 1)],
            "paragraphs": paragraphs, "tables": list(tables)}


def main() -> None:
    docs = {
        "CHG-104118/approval-email.layout.json": layout(2, [
            para("Meridian Freight Holdings - internal", 1, "pageHeader"),
            para("From: lpatel@meridianfreight.example", 1),
            para("To: dkwan@meridianfreight.example; change-board@meridianfreight.example", 1),
            para("Date: 2026-03-04T09:15:00-06:00", 1),
            para("Subject: RE: CHG-104118 Rate engine: fuel surcharge table v14", 1),
            para("Approved. CHG-104118 may be deployed in the 16:00 UTC window after the integration suite passes.", 1),
            para("Lakshmi Patel, Change Advisory Board", 1),
            para("This message may contain confidential information. If you received it in error, delete it.", 2),
            para("Page 2 of 2", 2, "pageNumber"),
        ]),
        "CAB/cab-minutes-2026-04-14.layout.json": layout(2, [
            para("Change Advisory Board - minutes", 1, "title"),
            para("Meeting held 2026-04-14 from 15:00 to 15:45 America/Chicago. Chair: T. Nguyen. Quorum present.", 1),
            para("Emergency changes reviewed after the fact are recorded with the time of the CAB decision.", 1),
            para("Decisions", 2, "sectionHeading"),
        ], [table(2, [
            ["Change", "Decision", "Decided at", "Chair"],
            ["CHG-104190", "approved", "2026-04-14T15:05:00-05:00", "T. Nguyen"],
            ["CHG-104201", "approved (retrospective)", "2026-04-14T15:30:00-05:00", "T. Nguyen"],
            ["CHG-104215", "deferred", "2026-04-14T15:40:00-05:00", "T. Nguyen"],
        ])]),
        "CHG-104300/approval-email.layout.json": layout(1, [
            para("From: tnguyen@meridianfreight.example", 1),
            para("Date: 2026-05-02T10:00:00-05:00", 1),
            para("Subject: CHG-104300 Billing export hotfix", 1),
            para("Approved for CHG-104300. CHG-104305 is not on this week's agenda; raise it at the next CAB.", 1),
        ]),
    }
    for name, doc in docs.items():
        p = OUT / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc, indent=1))
    csv = OUT / "deploy-logs" / "prod-deploys-2026H1.csv"
    csv.parent.mkdir(parents=True, exist_ok=True)
    csv.write_text("\n".join([
        "change_id,pr_number,environment,deployed_at,pipeline_run",
        "CHG-104102,2219,prod,2026-03-02T15:10:00Z,deploy-88011",
        "CHG-104118,2231,prod,2026-03-04T16:20:00Z,deploy-88120",
        "CHG-104190,2266,prod,2026-04-14T21:10:00Z,deploy-88690",
        "CHG-104201,2270,prod,2026-04-14T18:05:00Z,deploy-88677",
        "CHG-104300,2290,prod,2026-05-02T17:30:00Z,deploy-89410",
        "CHG-104305,2293,prod,2026-05-04T14:00:00Z,deploy-89433",
    ]) + "\n")
    (OUT / "CHG-104118" / "screenshot-deploy.docx").write_text("placeholder for a Word export; not parsed by ControlPilot\n")


if __name__ == "__main__":
    main()
