"""Raise the same anomaly's work order through a nasty link and list what the CMMS holds."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmms.client import CMMSClient  # noqa: E402
from cmms.fake import FakeClock, FakeCMMS, Transport  # noqa: E402

clock = FakeClock()
server = FakeCMMS(clock)
t = Transport(server)
c = CMMSClient(t, FakeCMMS.CLIENT_ID, FakeCMMS.CLIENT_SECRET, clock.time, clock.sleep)
t.script([None, "503", "commit-timeout", "429", None])
wo = c.raise_work_order("pump-04", "2026-11-04T14:05:00Z", "Outer race BPFO 21 dB above floor", "P2")
print("raised:", wo)
print("orders in CMMS for pump-04:", [o.id for o in c.list_work_orders("pump-04")])
print("slept:", [round(s, 2) for s in clock.sleeps], "requests:", len(t.calls))
