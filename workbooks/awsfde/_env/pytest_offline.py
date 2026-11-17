"""pytest plugin loaded by every awsfde test run (-p pytest_offline).

Blocks outbound network connections so that no test can reach AWS or any other service by
accident: moto, botocore Stubber and the exercise fakes all work without a socket. Loopback is
allowed for exercises that start a local HTTP server. Also sets fake AWS credentials and region
when they are missing, so boto3 clients can be built offline.
"""

from __future__ import annotations

import os
import socket

import pytest

for _k, _v in {
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SESSION_TOKEN": "testing",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_EC2_METADATA_DISABLED": "true",
}.items():
    os.environ.setdefault(_k, _v)
os.environ.pop("AWS_PROFILE", None)  # never a real profile in tests

_real_connect = socket.socket.connect
_LOOPBACK = ("127.0.0.1", "::1", "localhost")


def _guarded_connect(self, address):  # type: ignore[no-untyped-def]
    host = address[0] if isinstance(address, tuple) else address
    if isinstance(host, str) and (host in _LOOPBACK or host.startswith("127.") or self.family == socket.AF_UNIX):
        return _real_connect(self, address)
    raise OSError(f"network disabled in awsfde tests (attempted connect to {address!r})")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):  # type: ignore[no-untyped-def]
    socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
