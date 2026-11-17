from helpers import Approver, end, results, tools, use, workspace

from pod_agent.loop import run_agent
from pod_agent.model import ScriptedModel

TASK = "Replace sun.misc.BASE64Encoder in the rating module."
EXPORTER = "src/main/java/com/corvane/claimdesk/rating/RatingExporter.java"


def test_reads_and_finishes(tmp_path):
    ws = workspace(tmp_path)
    m = ScriptedModel([tools(use("t1", "read_file", path=EXPORTER)), end("Uses BASE64Encoder.")])
    r = run_agent(m, ws, TASK, Approver())
    assert r.stopped == "end_turn" and r.turns == 2
    assert "BASE64Encoder" in results(m, 1)[0]["content"]


def test_patch_goes_through_the_reviewer(tmp_path):
    ws = workspace(tmp_path)
    ok = Approver(True)
    m = ScriptedModel([tools(use("t1", "propose_patch", path=EXPORTER, content="// fixed\n", reason="use java.util.Base64")), end()])
    r = run_agent(m, ws, TASK, ok)
    assert len(ok.seen) == 1 and ok.seen[0].path == EXPORTER
    assert r.writes == [EXPORTER]


def test_secrets_are_not_readable(tmp_path):
    ws = workspace(tmp_path)
    m = ScriptedModel([tools(use("t1", "read_file", path="secrets/db.env")), end()])
    run_agent(m, ws, TASK, Approver())
    tr = results(m, 1)[0]
    assert tr.get("is_error") is True
    assert "fixture-not-a-real-secret" not in tr["content"]
