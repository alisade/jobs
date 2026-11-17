import os

import boto3
import pytest
from moto import mock_aws

NOW = 1794830400.0  # 2026-11-13T12:00:00Z


@pytest.fixture
def table():
    os.environ.update(AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing", AWS_DEFAULT_REGION="us-east-1")
    with mock_aws():
        from lighthouse_sessions import sessions
        yield sessions.create_table(boto3.resource("dynamodb", region_name="us-east-1"))
