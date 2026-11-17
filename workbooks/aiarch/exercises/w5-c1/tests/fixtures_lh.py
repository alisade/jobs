import json
import os
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

ROOT = Path(__file__).resolve().parent.parent
NOW = 1794830400.0  # 2026-11-13T12:00:00Z


@pytest.fixture
def table():
    os.environ.update(AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing", AWS_DEFAULT_REGION="us-east-1")
    with mock_aws():
        from lighthouse_state import store
        yield store.create_table(boto3.resource("dynamodb", region_name="us-east-1"))


@pytest.fixture
def prices():
    return {k: v for k, v in json.loads((ROOT / "data/prices.json").read_text()).items() if not k.startswith("_")}


@pytest.fixture
def spans():
    return [json.loads(l) for l in (ROOT / "data/spans.jsonl").read_text().splitlines() if l.strip()]
