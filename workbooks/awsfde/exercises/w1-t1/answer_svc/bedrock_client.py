"""bedrock-runtime client factory used by the answer Lambda."""

from __future__ import annotations

import boto3
from botocore.config import Config

# Release 2026.11.06 "resilience hardening": more SDK retries for Bedrock throttling (INC-4410).
SDK_RETRIES = {"max_attempts": 10, "mode": "standard"}


def make_client(region: str = "us-east-1"):
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(retries=SDK_RETRIES, connect_timeout=3, read_timeout=30),
    )
