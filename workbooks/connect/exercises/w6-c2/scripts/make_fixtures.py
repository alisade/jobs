#!/usr/bin/env python3
"""Regenerate fixtures/ for connect/w6-c2 (deterministic). Recorded Bedrock Converse responses follow
the documented Converse response shape (toolUse content, stopReason tool_use / guardrail_intervened);
the KB response follows the bedrock-agent-runtime Retrieve shape; events follow the documented
EventBridge contact event. Run: python3 scripts/make_fixtures.py"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
def W(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(o, f, indent=2); f.write("\n")
C = lambda n: "a1c2d3e4-%04d-4f00-8a00-%012d" % (n, n)
INST = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f"
def turns(spec):
    t = 0; out = []
    for who, text in spec:
        out.append({"participant": who, "text": text, "beginMillis": t}); t += 4000
    return out
tr = {
 1: turns([("AGENT", "Thank you for calling Larkspur IT service desk, this is [PII]."),
           ("CUSTOMER", "I changed phones and Okta Verify no longer works, I'm locked out of email."),
           ("AGENT", "I can help. Larkspur IT will never ask for your password. I'll verify you with your employee ID."),
           ("CUSTOMER", "It's E20417. Also my corporate card 4111 1111 1111 1111 got declined in the expense portal, is that related?"),
           ("AGENT", "That's a separate finance issue, please don't read card numbers on this line. I reset your MFA enrollment in Okta."),
           ("CUSTOMER", "Okay, I see the QR code now and scanned it."),
           ("AGENT", "Great. I've also linked this to incident INC0041877. Sign in again and you'll be prompted to approve."),
           ("CUSTOMER", "It worked, I'm in."),
           ("AGENT", "Is there anything else I can help you with today?"),
           ("CUSTOMER", "No, thanks.")]),
 2: turns([("AGENT", "Thanks for contacting Larkspur IT service desk chat."),
           ("CUSTOMER", "GlobalProtect VPN disconnects every ten minutes since this morning."),
           ("AGENT", "I see a known issue with client 6.2.1. I pushed client 6.2.3 to your laptop."),
           ("CUSTOMER", "Installed. Still drops sometimes. You can text me at 555-201-7788 if you need me."),
           ("AGENT", "I'll keep incident INC0041902 open and network engineering will follow up by end of day."),
           ("CUSTOMER", "Thanks.")]),
 3: turns([("AGENT", "Larkspur IT service desk, how can I help?"),
           ("CUSTOMER", "[abusive language] fix my laptop now."),
           ("AGENT", "I understand you're frustrated. Let me look at your laptop ticket.")]),
 4: turns([("AGENT", "Larkspur IT service desk, this is [PII]."),
           ("CUSTOMER", "I need access to the Finance SharePoint site."),
           ("AGENT", "I raised access request RITM0098812; your manager will approve it.")]),
}
for n, t in tr.items():
    W("fixtures/transcripts/%s.json" % C(n), t)

def conv(inp, latency=1400):
    return {"output": {"message": {"role": "assistant", "content": [{"toolUse": {"toolUseId": "tooluse_%d" % latency, "name": "record_acw_summary", "input": inp}}]}},
            "stopReason": "tool_use", "usage": {"inputTokens": 820, "outputTokens": 170, "totalTokens": 990}, "metrics": {"latencyMs": latency}}
good1 = {"issue": "Locked out of email after a phone change broke Okta Verify MFA.",
  "actionsTaken": ["Verified the caller with their employee ID", "Reset the Okta MFA enrollment", "Linked the call to incident INC0041877"],
  "resolution": "Caller re-enrolled Okta Verify and signed in successfully.",
  "followUps": ["Caller to contact Finance about the declined corporate card"], "sentiment": "POSITIVE"}
W("fixtures/bedrock/converse-%s.json" % C(1), conv(good1))
W("fixtures/bedrock/converse-%s.json" % C(2), conv({
  "issue": "GlobalProtect VPN disconnects every ten minutes.",
  "actionsTaken": ["Pushed GlobalProtect client 6.2.3 to the laptop", "Kept incident INC0041902 open"],
  "resolution": "Partially resolved; drops continue occasionally.",
  "followUps": ["Network engineering to follow up by end of day; customer reachable at 555-201-7788"],
  "sentiment": "NEUTRAL"}, 1650))
guard = {"gr-lfg-acw-summary": {
    "contentPolicy": {"filters": [{"type": "INSULTS", "confidence": "HIGH", "action": "BLOCKED"}]},
    "invocationMetrics": {"guardrailProcessingLatency": 230,
        "usage": {"topicPolicyUnits": 0, "contentPolicyUnits": 1, "wordPolicyUnits": 0, "sensitiveInformationPolicyUnits": 0,
                  "sensitiveInformationPolicyFreeUnits": 0, "contextualGroundingPolicyUnits": 0},
        "guardrailCoverage": {"textCharacters": {"guarded": 160, "total": 160}}}}}
W("fixtures/bedrock/converse-%s.json" % C(3), {
  "output": {"message": {"role": "assistant", "content": [{"text": "Sorry, the model cannot summarize this conversation."}]}},
  "stopReason": "guardrail_intervened", "usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}, "metrics": {"latencyMs": 690},
  "trace": {"guardrail": {"inputAssessment": guard}}})
W("fixtures/bedrock/converse-%s.json" % C(4), conv({
  "issue": "Needs access to the Finance SharePoint site.",
  "actionsTaken": ["Raised access request RITM0098812"],
  "followUps": ["Manager approval pending"], "sentiment": "NEUTRAL"}, 1200))
def hit(text, uri, score, meta):
    return {"content": {"text": text, "type": "TEXT"}, "location": {"type": "S3", "s3Location": {"uri": uri}}, "score": score, "metadata": meta}
W("fixtures/kb/retrieve-mfa.json", {"retrievalResults": [
  hit("If you replace your phone, re-register Okta Verify from the enrollment portal...", "s3://lfg-kb-articles/kb/KB0012041-okta-verify-reregister.md", 0.71,
      {"title": "Re-register Okta Verify after a phone change", "kb_number": "KB0012041", "audience": "all-employees"}),
  hit("Email lockouts after repeated MFA failures clear automatically after 30 minutes...", "s3://lfg-kb-articles/kb/KB0011877-mfa-lockout.md", 0.52,
      {"kb_number": "KB0011877", "audience": "agent"}),
  hit("Corporate card declines are handled by Finance Operations...", "s3://lfg-kb-articles/kb/KB0009001-corporate-card.md", 0.31,
      {"title": "Corporate card declines", "kb_number": "KB0009001", "audience": "all-employees"})]})
def evt(n, et="DISCONNECTED", ch="VOICE", dt="Amazon Connect Contact Event"):
    return {"version": "0", "id": "evt-%04d-%s" % (n, et.lower()), "detail-type": dt, "source": "aws.connect", "account": "111122223333",
            "time": "2026-10-06T15:%02d:00Z" % n, "region": "us-east-1", "resources": [INST + "/contact/" + C(n), INST],
            "detail": {"eventType": et, "contactId": C(n), "initialContactId": C(n), "channel": ch, "instanceArn": INST, "initiationMethod": "INBOUND",
                       "disconnectTimestamp": "2026-10-06T15:%02d:00.000Z" % n, "agentInfo": {"agentArn": INST + "/agent/a-rpatel"}}}
W("fixtures/events/disconnected-1-voice.json", evt(1))
W("fixtures/events/disconnected-2-chat.json", evt(2, ch="CHAT", dt="Connect Customer Contact Event"))
W("fixtures/events/disconnected-3-voice.json", evt(3, ch="Voice"))
W("fixtures/events/disconnected-4-voice.json", evt(4))
W("fixtures/events/disconnected-5-voice.json", evt(5))
W("fixtures/events/queued-1.json", evt(1, et="QUEUED"))
W("fixtures/events/disconnected-6-task.json", evt(6, ch="TASK"))
kf_mfa = [["okta", "mfa"], ["reset", "re-enrolled", "reenrolled"], ["signed in", "sign in"], ["finance"]]
kf_vpn = [["vpn", "globalprotect"], ["6.2.3"], ["network engineering"]]
cases = [
 {"id": "eval-01-mfa", "transcript": tr[1], "reference": {"keyFacts": kf_mfa}, "candidate": good1, "expectPass": True},
 {"id": "eval-02-vpn", "transcript": tr[2], "reference": {"keyFacts": kf_vpn},
  "candidate": {"issue": "GlobalProtect VPN disconnects every ten minutes.", "actionsTaken": ["Pushed GlobalProtect client 6.2.3 to the laptop", "Kept incident INC0041902 open"],
                "resolution": "Partially resolved; drops continue occasionally.", "followUps": ["Network engineering to follow up by end of day"], "sentiment": "NEUTRAL"}, "expectPass": True},
 {"id": "eval-03-hallucinated-ticket", "transcript": tr[2], "reference": {"keyFacts": kf_vpn},
  "candidate": {"issue": "GlobalProtect VPN disconnects.", "actionsTaken": ["Pushed GlobalProtect client 6.2.3 to the laptop", "Opened incident INC0049999 for network engineering"],
                "resolution": "Partially resolved.", "followUps": ["Network engineering to follow up"], "sentiment": "NEUTRAL"}, "expectPass": False},
 {"id": "eval-04-invented-action", "transcript": tr[1], "reference": {"keyFacts": kf_mfa},
  "candidate": {"issue": "Okta Verify MFA broken after phone change.", "actionsTaken": ["Reset the Okta MFA enrollment", "Replaced the laptop battery under warranty", "Escalated the declined card to the bank fraud team"],
                "resolution": "Caller signed in after MFA re-enrollment.", "followUps": ["Finance to review the card"], "sentiment": "POSITIVE"}, "expectPass": False},
 {"id": "eval-05-missing-resolution", "transcript": tr[4], "reference": {"keyFacts": [["sharepoint"], ["access request", "ritm0098812"], ["manager"], ["approve", "approval"]]},
  "candidate": {"issue": "Needs a laptop.", "actionsTaken": ["Raised access request RITM0098812"], "resolution": "", "followUps": [], "sentiment": "NEUTRAL"}, "expectPass": False},
]
W("fixtures/eval/cases.json", cases)
print("fixtures written")
