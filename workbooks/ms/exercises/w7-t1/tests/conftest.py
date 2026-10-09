import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture()
def flow():
    files = sorted((ROOT / "solution" / "Workflows").glob("ContosoPartsPOSync-*.json"))
    assert len(files) == 1, "exactly one ContosoPartsPOSync-*.json expected in solution/Workflows"
    return json.loads(files[0].read_text())


@pytest.fixture()
def definition(flow):
    return flow["properties"]["definition"]
