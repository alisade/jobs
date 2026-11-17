"""Generate data/sample-ctrs.jsonl and data/agent_staffing.csv (deterministic, seed 7).

Contact records follow the Amazon Connect contact record data model (subset): ContactId, Channel,
InitiationMethod, InitiationTimestamp, DisconnectTimestamp, CustomerEndpoint, Queue, Agent,
Attributes, Recording, DisconnectReason. Run: python scripts/gen_sample.py
"""
import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

rnd = random.Random(7)
root = Path(__file__).resolve().parent.parent
QUEUES = ["GeneralSupport", "PasswordReset", "VIPDesk"]
AGENTS = ["aisha.k", "bruno.m", "chen.l", "dmitri.v", "elena.r"]
ARN = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f"


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def contact(i, day):
    start = datetime(2026, 10, day, 13, 0, tzinfo=timezone.utc) + timedelta(seconds=rnd.randint(0, 8 * 3600))
    channel = rnd.choices(["VOICE", "CHAT"], [0.7, 0.3])[0]
    cid = str(uuid.UUID(int=rnd.getrandbits(128)))
    attrs = {"lexIntent": rnd.choice(["ResetPassword", "VpnIssue", "AccessRequest", "Unknown"]), "callerVerified": rnd.choice(["true", "false"])}
    rec = {
        "AWSAccountId": "111122223333",
        "AWSContactTraceRecordFormatVersion": "2017-03-10",
        "InstanceARN": ARN,
        "ContactId": cid,
        "InitialContactId": cid,
        "Channel": channel,
        "InitiationMethod": "INBOUND" if channel == "VOICE" else "API",
        "InitiationTimestamp": iso(start),
        "CustomerEndpoint": {"Address": "+1212555%04d" % rnd.randint(0, 9999), "Type": "TELEPHONE_NUMBER"} if channel == "VOICE" else None,
        "SystemEndpoint": {"Address": "+18005550142", "Type": "TELEPHONE_NUMBER"} if channel == "VOICE" else None,
        "Attributes": attrs,
        "Queue": None,
        "Agent": None,
        "Recording": None,
        "DisconnectReason": "CUSTOMER_DISCONNECT",
    }
    kind = rnd.choices(["selfservice", "answered", "abandoned"], [0.25, 0.6, 0.15])[0]
    t = start + timedelta(seconds=rnd.randint(20, 90))
    if kind == "selfservice":
        attrs["selfServiceOutcome"] = "resolved"
    else:
        q = rnd.choices(QUEUES, [0.6, 0.3, 0.1])[0]
        wait = rnd.choice([5, 12, 25, 40, 55, 70, 95, 140, 200, 3])
        enq = t
        deq = t + timedelta(seconds=wait)
        rec["Queue"] = {"Name": q, "ARN": ARN + "/queue/q-" + q.lower(), "EnqueueTimestamp": iso(enq), "DequeueTimestamp": iso(deq), "Duration": wait}
        t = deq
        if kind == "answered":
            talk, hold, acw = rnd.randint(120, 900), rnd.choice([0, 0, 30, 90]), rnd.randint(20, 180)
            rec["Agent"] = {
                "Username": rnd.choice(AGENTS),
                "ConnectedToAgentTimestamp": iso(deq),
                "AgentInteractionDuration": talk,
                "CustomerHoldDuration": hold,
                "AfterContactWorkDuration": acw,
                "NumberOfHolds": 1 if hold else 0,
            }
            t = deq + timedelta(seconds=talk + hold)
            if channel == "VOICE":
                rec["Recording"] = {"Location": "lfg-connect-recordings/connect/lfg/CallRecordings/2026/10/%02d/%s.wav" % (day, cid), "Status": "AVAILABLE", "Type": "AUDIO"}
            rec["DisconnectReason"] = rnd.choice(["CUSTOMER_DISCONNECT", "AGENT_DISCONNECT"])
    rec["DisconnectTimestamp"] = iso(t)
    # a few realistic data-quality and compliance problems
    if i % 23 == 0:
        attrs["cardNumber"] = "4111 1111 1111 1111"
    if i % 29 == 0:
        attrs["notes"] = "caller read SSN 123-45-6789 to the bot"
    if i % 31 == 0:
        attrs["legalHold"] = "true"
    if i % 37 == 0:
        attrs["synthetic"] = "true"
    return rec


rows = [contact(i, 6 + (i % 3)) for i in range(1, 181)]
with open(root / "data" / "sample-ctrs.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
with open(root / "data" / "agent_staffing.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["agent_username", "dt", "staffed_seconds"])
    for d in (6, 7, 8):
        for a in AGENTS:
            w.writerow([a, "2026-10-%02d" % d, 8 * 3600 - rnd.randint(0, 3600)])
print("wrote", len(rows), "contact records")
