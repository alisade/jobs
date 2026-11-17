import json
from pathlib import Path

import pytest

from retrieval.rerank import StubReranker
from retrieval.search import HybridRetriever

FIX = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture(scope="session")
def docs():
    return json.loads((FIX / "corpus.json").read_text())


@pytest.fixture(scope="session")
def queries():
    return json.loads((FIX / "queries.json").read_text())


@pytest.fixture
def retriever(docs):
    return HybridRetriever(docs, reranker=StubReranker())
