import json
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from pa_graph.graph import build_graph
from pa_graph.model import ScriptedChatModel
from pa_graph.tools import FakeFhirStore

FIX = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def cases():
    return {c["case_id"]: c for c in json.loads((FIX / "cases.json").read_text())}


@pytest.fixture
def model():
    return ScriptedChatModel.from_file(FIX / "model_responses.json")


@pytest.fixture
def fhir():
    return FakeFhirStore(FIX / "fhir.json")


@pytest.fixture
def graph(model, fhir):
    return build_graph(model, fhir, checkpointer=InMemorySaver())
