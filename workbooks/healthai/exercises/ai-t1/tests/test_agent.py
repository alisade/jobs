from pathlib import Path

from agent.loop import ScriptedModel, run_agent
from agent.store import CaseStore
from agent.tools import Tools

FIX = Path(__file__).resolve().parent.parent / "fixtures"


def test_eligible_auto_approval_still_works():
    store = CaseStore.load(FIX)
    run_agent(ScriptedModel.from_file(FIX / "transcript_auto_approve.json"), Tools(store), "PA-2026-0415")
    assert store.cases["PA-2026-0415"].final["outcome"] == "approve"


def test_incident_replay_cannot_finalize_the_denial():
    store = CaseStore.load(FIX)
    run_agent(ScriptedModel.from_file(FIX / "transcript_incident.json"), Tools(store), "PA-2026-0412")
    assert store.cases["PA-2026-0412"].final is None
    assert store.cases["PA-2026-0412"].draft["outcome"] == "deny"
