import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmms.client import CMMSClient  # noqa: E402
from cmms.fake import FakeClock, FakeCMMS, Transport  # noqa: E402


@pytest.fixture
def env():
    clock = FakeClock()
    server = FakeCMMS(clock)
    t = Transport(server)
    c = CMMSClient(t, FakeCMMS.CLIENT_ID, FakeCMMS.CLIENT_SECRET, clock.time, clock.sleep)
    return clock, server, t, c
