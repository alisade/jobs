#!/usr/bin/env python3
"""Generate the incident bundle for modernize/w2-t1: repo/ (a synthetic ClaimDesk checkout with three
modules) and incident/ (the agent transcript, the spec it produced, the draft postmortem).
Deterministic: same output every run."""

from __future__ import annotations

import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE / "repo"
INC = HERE / "incident"

CORE_TABLES = ["CLAIM", "CLAIM_NOTE", "CLAIM_PARTY", "RESERVE_LINE", "PAYMENT", "POLICY_REF", "ADJUSTER", "USER_ROLE"]
WEB_TABLES = ["CLAIM", "CLAIM_NOTE", "USER_ROLE", "SAVED_SEARCH"]
BATCH_TABLES = ["LOSS_TRIANGLE", "IBNR_FACTOR", "REINS_TREATY", "BORDEREAU_RUN", "CLAIM", "RESERVE_LINE"]
VERBS = ["SELECT {cols} FROM {t} WHERE CLAIM_NUMBER = ?", "UPDATE {t} SET STATUS = ? WHERE ID = ?",
         "INSERT INTO {t} (ID, CLAIM_NUMBER, CREATED) VALUES (?, ?, SYSDATE)",
         "SELECT c.CLAIM_NUMBER FROM CLAIM c JOIN {t} x ON x.CLAIM_NUMBER = c.CLAIM_NUMBER"]


def java_dao(pkg: str, cls: str, tables: list[str], n: int, rnd: random.Random) -> str:
    out = [f"package {pkg};", "", "import java.sql.Connection;", "import java.sql.PreparedStatement;", "",
           f"public class {cls} {{", ""]
    for i in range(n):
        t = rnd.choice(tables)
        sql = rnd.choice(VERBS).format(t=t, cols="ID, CLAIM_NUMBER, STATUS")
        out += [f"    public void op{i}(Connection c) throws Exception {{",
                f"        try (PreparedStatement ps = c.prepareStatement(\"{sql}\")) {{",
                "            ps.execute();", "        }", "    }", ""]
    out.append("}")
    return "\n".join(out) + "\n"


def build_repo() -> None:
    rnd = random.Random(20261113)
    if REPO.exists():
        shutil.rmtree(REPO)
    specs = [
        ("claims-core", "com/corvane/claimdesk/core/dao", "com.corvane.claimdesk.core.dao", CORE_TABLES,
         ["ClaimDao", "NoteDao", "PartyDao", "ReserveDao", "PaymentDao", "PolicyRefDao", "AdjusterDao", "RoleDao", "SearchSupport", "AuditDao"], 15),
        ("claims-web", "com/corvane/claimdesk/web/dao", "com.corvane.claimdesk.web.dao", WEB_TABLES,
         ["SearchDao", "WebNoteDao", "SessionRoleDao", "DashboardDao"], 15),
        ("reporting-batch", "com/corvane/claimdesk/reporting", "com.corvane.claimdesk.reporting", BATCH_TABLES,
         ["IbnrJob", "TriangleBuilder", "TreatyLoader", "BordereauJob"], 12),
    ]
    for module, path, pkg, tables, classes, ops in specs:
        base = REPO / module / "src/main/java" / path
        base.mkdir(parents=True)
        (REPO / module / "pom.xml").write_text(
            f"<project><modelVersion>4.0.0</modelVersion><groupId>com.corvane.claimdesk</groupId>"
            f"<artifactId>{module}</artifactId><version>7.4.2</version></project>\n")
        for cls in classes:
            (base / f"{cls}.java").write_text(java_dao(pkg, cls, tables, ops, rnd))
    res = REPO / "reporting-batch/src/main/resources"
    res.mkdir(parents=True)
    (res / "ibnr.sql").write_text(
        "-- month-end IBNR, run by IbnrJob\n"
        "INSERT INTO IBNR_RESULT (RUN_ID, LOB, AMOUNT)\n"
        "SELECT ?, t.LOB, SUM(t.PAID * f.FACTOR) FROM LOSS_TRIANGLE t JOIN IBNR_FACTOR f ON f.LOB = t.LOB GROUP BY t.LOB;\n")
    (REPO / "pom.xml").write_text("<project><modelVersion>4.0.0</modelVersion><packaging>pom</packaging><modules>"
                                  "<module>claims-core</module><module>claims-web</module><module>reporting-batch</module>"
                                  "</modules></project>\n")


def build_incident() -> None:
    if INC.exists():
        shutil.rmtree(INC)
    INC.mkdir()
    scan = HERE / "skill/reverse-engineer/scripts/scan_db.py"
    # what the skill's tool printed during the run: the 2026-10-28 version of scan_db.py (the starter)
    out = subprocess.run([sys.executable, str(HERE / "scripts/scan_db_v1.py"), str(REPO)],
                         capture_output=True, text=True, check=True).stdout
    shown = sorted({line.split()[1] for line in out.splitlines() if line.strip()})
    events = [
        {"ts": "2026-10-28T14:02:11Z", "type": "user", "text": "Reverse engineer the ClaimDesk checkout in repo/ for the EAP 8 pod. Use the reverse-engineer skill."},
        {"ts": "2026-10-28T14:02:12Z", "type": "skill", "name": "reverse-engineer", "loaded": True},
        {"ts": "2026-10-28T14:02:19Z", "type": "tool_use", "tool": "Bash", "input": {"command": "python3 skill/reverse-engineer/scripts/scan_db.py repo"}},
        {"ts": "2026-10-28T14:02:20Z", "type": "tool_result", "tool": "Bash", "exit_code": 0, "lines": len(out.splitlines()), "chars": len(out), "output": out},
        {"ts": "2026-10-28T14:02:41Z", "type": "assistant", "text": "The scan found " + str(len(shown)) + " tables: " + ", ".join(shown)
         + ". All database access is in claims-core and claims-web; reporting-batch has no direct database access (it only reads files)."},
        {"ts": "2026-10-28T14:05:02Z", "type": "tool_use", "tool": "Write", "input": {"file_path": "spec/inventory.json"}},
        {"ts": "2026-10-28T14:09:30Z", "type": "assistant", "text": "Inventory and spec written. Every table cites file:line from the scan."},
        {"ts": "2026-10-28T14:09:30Z", "type": "run_stats", "context_used_pct": 31, "input_tokens": 61822, "output_tokens": 4210, "model_turns": 9},
    ]
    with (INC / "transcript.jsonl").open("w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    (INC / "spec-excerpt.md").write_text(
        "## 3. Data: database touchpoints (from the reverse-engineer run, 2026-10-28)\n\n"
        "| Table | Modules |\n|---|---|\n" + "".join(f"| {t} | claims-core, claims-web |\n" for t in shown)
        + "\nreporting-batch: no database access (reads files only). Not in scope for the schema migration.\n")
    (INC / "PAGE.txt").write_text(
        "INCIDENT INC-7731  P2  2026-11-12 06:40 ET  month-end IBNR run failed in the EAP 8 rehearsal\n"
        "ORA-00942: table or view does not exist (LOSS_TRIANGLE) from reporting-batch IbnrJob.\n"
        "The migration plan, built from the reverse-engineer spec, never granted or migrated\n"
        "LOSS_TRIANGLE, IBNR_FACTOR, REINS_TREATY, BORDEREAU_RUN or IBNR_RESULT. The spec says\n"
        "reporting-batch has no database access. Actuarial close is in 9 days.\n")
    (INC / "postmortem-draft.md").write_text(
        "# INC-7731 postmortem (DRAFT, author: pod dev)\n\n"
        "Root cause: the model hallucinated that reporting-batch has no database access, probably because\n"
        "the context window filled up on a big repo. Action: use a bigger model and tell it in the skill\n"
        "to be more careful.\n")


def main() -> int:
    build_repo()
    build_incident()
    print("bundle: repo/ and incident/ generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
