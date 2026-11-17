"""bedrock-runtime client factory used by the answer Lambda."""

from __future__ import annotations

import boto3
from botocore.config import Config

# The ONLY retry layer for Bedrock calls. total_max_attempts counts the first attempt
# (Config's "max_attempts" counts retries, so max_attempts=10 meant 11 attempts).
# Standard mode backs off with full jitter: rand(0,1) * min(2 ** n, 20) seconds.
SDK_RETRIES = {"total_max_attempts": 3, "mode": "standard"}


def make_client(region: str = "us-east-1"):
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(retries=SDK_RETRIES, connect_timeout=3, read_timeout=30),
    )
