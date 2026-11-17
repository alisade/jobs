"""bedrock-runtime client factory used by the answer Lambda."""

from __future__ import annotations

import boto3
from botocore.config import Config

SDK_RETRIES = {"max_attempts": 2, "mode": "standard"}


def make_client(region: str = "us-east-1"):
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(retries=SDK_RETRIES, connect_timeout=3, read_timeout=30),
    )
