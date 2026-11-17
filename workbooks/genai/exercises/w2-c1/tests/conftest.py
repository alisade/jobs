import pytest
from fastapi.testclient import TestClient

from catalog.app import create_app
from catalog.db import make_engine


@pytest.fixture
def client():
    with TestClient(create_app(make_engine())) as c:
        yield c
