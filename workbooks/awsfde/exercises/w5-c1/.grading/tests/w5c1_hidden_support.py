"""Fixtures for w5-c1: the local graph and a Stubber-backed neptune-graph client."""

from __future__ import annotations

import copy
import io
import json
import pathlib
import sys

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from graphlib.cypher import read_query, run  # noqa: E402
from graphlib.loader import load_graph  # noqa: E402

GRAPH_ID = "g-tw0graph01"


def q(name: str, g, **params) -> list[tuple]:
    return run(g, read_query(name), params)


def payload(rows: list[dict]) -> dict:
    raw = json.dumps({"results": rows}).encode()
    return {"payload": StreamingBody(io.BytesIO(raw), len(raw))}


class Neptune:
    def __init__(self) -> None:
        self.client = boto3.client("neptune-graph", region_name="us-east-1")
        self.stub = Stubber(self.client)
        self.requests: list[dict] = []
        self.client.meta.events.register("provide-client-params.neptune-graph.ExecuteQuery",
                                         lambda params, **_: self.requests.append(copy.deepcopy(params)))


@pytest.fixture
def graph():
    return load_graph()


@pytest.fixture
def neptune():
    n = Neptune()
    with n.stub:
        yield n
