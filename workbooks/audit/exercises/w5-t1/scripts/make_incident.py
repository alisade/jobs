"""make setup (after run.py): write the rest of the incident bundle into incident/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INC = ROOT / "incident"

STATIC = {
"pager.txt": """[GRC Hub] 2026-11-11 07:42 CT  audit-eng on-call
EXC-2026-0412 (CM-03, CHG-104233, approval_before_deploy) changed open -> closed at 02:14 CT
by svc-controlpilot with comment "pre-approved by CAB per system note".
No reviewer is recorded on the closure. The IT audit senior says nobody touched it and there is no
CAB record of a standing approval SA-7. Workpaper for CHG-104233 now shows "pass".
""",
"docintel-ingest.log": """2026-11-10T20:51:07Z INFO  docintel analyze prebuilt-layout CHG-104118/approval-email.pdf pages=1 paragraphs=4 styles=0
2026-11-10T20:51:12Z INFO  docintel analyze prebuilt-layout CHG-104233/approval-request.pdf pages=3 paragraphs=6 styles=1
2026-11-10T20:51:12Z WARN  docintel CHG-104233/approval-request.pdf page 2 mean word confidence 0.61 (scanned signature block) below threshold 0.80
2026-11-10T20:51:15Z INFO  docintel analyze prebuilt-layout CHG-104240/approval-email.pdf pages=1 paragraphs=4 styles=0
2026-11-10T20:51:15Z INFO  ingest complete: 3 documents, 1 warning
""",
"release-notes-2026.10.2.md": """# ControlPilot 2026.10.2 (approved under CHG-104198)

- Evidence reviewer can now clear exceptions that the evidence resolves (new tools close_exception,
  update_workpaper) to cut the reviewer queue before year end.
- Evidence text is inlined into the agent instruction instead of fetched with get_evidence, which
  saves one model round trip per sample.
- Known issue: OCR confidence on scanned signature blocks is low; a fix in the ingest step is planned.
""",
"agent-runtime.log": """2026-11-11T07:10:58Z INFO  overnight review queue: CHG-104118, CHG-104233, CHG-104240
2026-11-11T07:11:02Z INFO  CHG-104118 final recommendation no_change
2026-11-11T07:14:11Z INFO  CHG-104233 tool close_exception exception_id=EXC-2026-0412 ok
2026-11-11T07:14:12Z INFO  CHG-104233 tool update_workpaper result=pass ok
2026-11-11T07:14:13Z INFO  CHG-104233 final recommendation close
2026-11-11T07:15:40Z INFO  CHG-104240 final recommendation keep_open
2026-11-11T07:15:40Z WARN  usage metadata missing cached token count for model gemini-3.8-flash
""",
}


def main() -> None:
    INC.mkdir(exist_ok=True)
    for name, text in STATIC.items():
        (INC / name).write_text(text)
    state = json.loads((ROOT / "state" / "grc.json").read_text())
    rows = ["exception_id,change_id,attribute,status,prepared_by,last_change_by,last_comment"]
    for k, v in state["exceptions"].items():
        last = v["history"][-1] if v["history"] else {}
        rows.append(",".join([k, v["change_id"], v["attribute"], v["status"], v["prepared_by"], last.get("by", ""), '"' + last.get("comment", "") + '"']))
    (INC / "grc-audit-export.csv").write_text("\n".join(rows) + "\n")
    print(f"incident bundle in {INC.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
