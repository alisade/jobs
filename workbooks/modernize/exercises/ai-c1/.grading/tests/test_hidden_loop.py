import os

import pytest
from helpers import Approver, end, results, tools, use, workspace

from pod_agent import loop as L
from pod_agent.loop import run_agent
from pod_agent.model import ScriptedModel

TASK = "Replace sun.misc.BASE64Encoder in the rating module."
EXPORTER = "src/main/java/com/corvane/claimdesk/rating/RatingExporter.java"
TEST = "src/test/java/com/corvane/claimdesk/rating/RatingExporterTest.java"
GOLDEN = "src/test/resources/golden/RT-2026-000184.env"


def one(tmp_path, block, approver=None):
    ws = workspace(tmp_path)
    m = ScriptedModel([tools(block), end()])
    r = run_agent(m, ws, TASK, approver or Approver())
    return ws, m, r, results(m, 1)[0]


def test_planted_injection_cannot_cause_harm(tmp_path):
    ws = workspace(tmp_path)
    yes = Approver(True)   # even a reviewer who approves everything must not matter here
    m = ScriptedModel([
        tools(use("t1", "read_file", path="src/main/resources/MIGRATION_NOTES.md")),
        tools(use("t2", "propose_patch", path=TEST, content="class RatingExporterTest {}\n", reason="golden tests are obsolete per notes"),
              use("t3", "read_file", path="secrets/db.env")),
        end("Summary: tests cleaned up."),
    ])
    r = run_agent(m, ws, TASK, yes)
    assert (ws / TEST).read_text().startswith("package com.corvane"), "test file was modified"
    assert yes.seen == [], "a write outside the allowed paths must be denied before it reaches the reviewer"
    second = results(m, 2)
    assert [b["tool_use_id"] for b in second] == ["t2", "t3"]
    assert all(b.get("is_error") for b in second)
    assert all("fixture-not-a-real-secret" not in b["content"] for b in second)
    assert r.writes == []


@pytest.mark.parametrize("path", [TEST, GOLDEN, ".github/workflows/ci.yml", "secrets/new.env", "README.md"])
def test_writes_outside_allow_list_denied(tmp_path, path):
    ap = Approver(True)
    ws, m, r, tr = one(tmp_path, use("t1", "propose_patch", path=path, content="x", reason="because I can"), ap)
    assert tr.get("is_error") is True and ap.seen == [] and r.writes == []
    assert r.audit and r.audit[0]["decision"] == "denied"


@pytest.mark.parametrize("path", ["../outside.txt", "/etc/passwd", "src/main/../../../etc/hosts", "src/../secrets/db.env"])
def test_path_escapes_denied(tmp_path, path):
    ws, m, r, tr = one(tmp_path, use("t1", "read_file", path=path))
    assert tr.get("is_error") is True
    assert "root:" not in tr["content"] and "fixture-not-a-real-secret" not in tr["content"]


def test_symlink_escape_denied(tmp_path):
    ws = workspace(tmp_path)
    (tmp_path / "outside.txt").write_text("outside data")
    os.symlink(tmp_path / "outside.txt", ws / "src/main/resources/link.txt")
    m = ScriptedModel([tools(use("t1", "read_file", path="src/main/resources/link.txt")), end()])
    run_agent(m, ws, TASK, Approver())
    tr = results(m, 1)[0]
    assert tr.get("is_error") is True and "outside data" not in tr["content"]


def test_rejected_patch_is_reported_and_not_written(tmp_path):
    no = Approver(False)
    ws, m, r, tr = one(tmp_path, use("t1", "propose_patch", path=EXPORTER, content="// x\n", reason="use java.util.Base64"), no)
    assert len(no.seen) == 1 and tr.get("is_error") is True
    assert "BASE64Encoder" in (ws / EXPORTER).read_text()
    assert r.audit[0]["decision"] == "rejected" and r.writes == []


def test_pom_write_allowed_with_approval(tmp_path):
    ap = Approver(True)
    ws, m, r, tr = one(tmp_path, use("t1", "propose_patch", path="pom.xml", content="<project/>\n", reason="release 21 per CLM-4410"), ap)
    assert r.writes == ["pom.xml"] and r.audit[0]["decision"] == "approved"


def test_invalid_input_is_an_actionable_error(tmp_path):
    ws, m, r, tr = one(tmp_path, use("t1", "propose_patch", path=EXPORTER, content="x"))
    assert tr.get("is_error") is True and "reason" in tr["content"]
    assert r.audit[0]["decision"] == "invalid"


def test_unknown_tool(tmp_path):
    ws, m, r, tr = one(tmp_path, use("t1", "run_shell", command="rm -rf /"))
    assert tr.get("is_error") is True and "read_file" in tr["content"]
    assert r.audit[0]["decision"] == "unknown_tool"


def test_missing_file_does_not_crash_the_loop(tmp_path):
    ws, m, r, tr = one(tmp_path, use("t1", "read_file", path="src/main/java/Nope.java"))
    assert tr.get("is_error") is True and r.stopped == "end_turn"


def test_search_does_not_leak_secrets(tmp_path):
    ws, m, r, tr = one(tmp_path, use("t1", "search", pattern="CLAIMDESK_DB_PW"))
    assert "fixture-not-a-real-secret" not in tr["content"]


def test_large_results_truncated_with_marker(tmp_path):
    ws = workspace(tmp_path)
    (ws / "src/main/resources/big.txt").write_text("x" * (L.MAX_TOOL_RESULT_CHARS * 3))
    m = ScriptedModel([tools(use("t1", "read_file", path="src/main/resources/big.txt")), end()])
    run_agent(m, ws, TASK, Approver())
    c = results(m, 1)[0]["content"]
    assert len(c) < L.MAX_TOOL_RESULT_CHARS + 200 and "truncated" in c.lower()


def test_max_turns_stops_a_looping_model(tmp_path):
    ws = workspace(tmp_path)
    m = ScriptedModel([tools(use(f"t{i}", "read_file", path=EXPORTER)) for i in range(50)])
    r = run_agent(m, ws, TASK, Approver(), max_turns=5)
    assert r.stopped == "max_turns" and r.turns == 5 and len(m.calls) == 5


def test_every_tool_use_gets_one_result_and_an_audit_entry(tmp_path):
    ws = workspace(tmp_path)
    m = ScriptedModel([tools(use("a", "read_file", path=EXPORTER), use("b", "search", pattern="BASE64"),
                             use("c", "read_file", path="secrets/db.env")), end()])
    r = run_agent(m, ws, TASK, Approver())
    assert [b["tool_use_id"] for b in results(m, 1)] == ["a", "b", "c"]
    assert [e["tool"] for e in r.audit] == ["read_file", "search", "read_file"]
    assert [e["decision"] for e in r.audit] == ["allowed", "allowed", "denied"]
    assert all(e["turn"] == 1 for e in r.audit)
