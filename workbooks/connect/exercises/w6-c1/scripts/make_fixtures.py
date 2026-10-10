#!/usr/bin/env python3
"""Regenerate fixtures/ for connect/w6-c1 (deterministic). The files follow the documented
conversational analytics (Contact Lens) post-contact output schema (Version 1.1.0) and the
real-time segment stream schema (Version 1.0.0). Run: python3 scripts/make_fixtures.py"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNT = "111122223333"
INSTANCE = "5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f"
ENTITIES = ["CREDIT_DEBIT_NUMBER", "NAME", "USERNAME", "PASSWORD", "PHONE", "EMAIL"]

def cid(n):
    return "4c1d2e3f-%04d-4a5b-9c8d-%012d" % (n, n)

def turns(spec):
    out, t = [], 0
    for i, (who, text, sent, dur) in enumerate(spec):
        turn = {"BeginOffsetMillis": t, "Content": text, "EndOffsetMillis": t + dur,
                "Id": "t%02d-%s" % (i, who.lower()), "ParticipantId": who, "Sentiment": sent,
                "LoudnessScore": [70.1 + (i % 5), 72.4]}
        if "[PII]" in text:
            turn["Redaction"] = {"RedactedTimestamps": [{"BeginOffsetMillis": t + 400, "EndOffsetMillis": t + 900}]}
        if who == "CUSTOMER" and sent == "NEGATIVE" and i < 4:
            turn["IssuesDetected"] = [{"CharacterOffsets": {"BeginOffsetChar": 0, "EndOffsetChar": len(text)}, "Text": text}]
        out.append(turn)
        t += dur + 300
    return out, t

def quarters(total, scores):
    q = total // 4
    return [{"BeginOffsetMillis": i * q, "EndOffsetMillis": (i + 1) * q, "Score": s} for i, s in enumerate(scores)]

def analysis(n, spec, overall, cust_q, agent_q, categories=(), output="Redacted", channel="VOICE",
             job="COMPLETED", interruptions_agent=0, nontalk=0):
    tr, total = turns(spec)
    agent_talk = sum(x["EndOffsetMillis"] - x["BeginOffsetMillis"] for x in tr if x["ParticipantId"] == "AGENT")
    cust_talk = sum(x["EndOffsetMillis"] - x["BeginOffsetMillis"] for x in tr if x["ParticipantId"] == "CUSTOMER")
    meta = {"Output": output}
    if output == "Redacted":
        meta["RedactionTypes"] = ["PII"]
        meta["RedactionTypesMetadata"] = {"PII": {"RedactionEntitiesRequested": ENTITIES, "RedactionMaskMode": "PII"}}
    doc = {
        "Version": "1.1.0", "AccountId": ACCOUNT, "Channel": channel, "ContentMetadata": meta,
        "JobStatus": job, "LanguageCode": "en-US",
        "Participants": [{"ParticipantId": "CUSTOMER", "ParticipantRole": "CUSTOMER"}, {"ParticipantId": "AGENT", "ParticipantRole": "AGENT"}],
        "Categories": {"MatchedCategories": list(categories), "MatchedDetails": {c: {"PointsOfInterest": [{"BeginOffsetMillis": 0, "EndOffsetMillis": 4000}]} for c in categories}},
        "ConversationCharacteristics": {
            "TotalConversationDurationMillis": total,
            "Sentiment": {"OverallSentiment": {"AGENT": overall[0], "CUSTOMER": overall[1]},
                          "SentimentByPeriod": {"QUARTER": {"AGENT": quarters(total, agent_q), "CUSTOMER": quarters(total, cust_q)}}},
            "Interruptions": {"InterruptionsByInterrupter": {"AGENT": [{"BeginOffsetMillis": 5000 + k * 7000, "DurationMillis": 1200, "EndOffsetMillis": 6200 + k * 7000} for k in range(interruptions_agent)]},
                              "TotalCount": interruptions_agent, "TotalTimeMillis": 1200 * interruptions_agent},
            "NonTalkTime": {"TotalTimeMillis": nontalk, "Instances": ([{"BeginOffsetMillis": 20000, "DurationMillis": nontalk, "EndOffsetMillis": 20000 + nontalk}] if nontalk else [])},
            "TalkSpeed": {"DetailsByParticipant": {"AGENT": {"AverageWordsPerMinute": 168}, "CUSTOMER": {"AverageWordsPerMinute": 151}}},
            "TalkTime": {"TotalTimeMillis": agent_talk + cust_talk, "DetailsByParticipant": {"AGENT": {"TotalTimeMillis": agent_talk}, "CUSTOMER": {"TotalTimeMillis": cust_talk}}},
        },
        "CustomModels": [],
        "Transcript": tr,
    }
    if channel == "CHAT":
        for x in doc["Transcript"]:
            x.pop("LoudnessScore", None)
        doc["ConversationCharacteristics"] = {k: v for k, v in doc["ConversationCharacteristics"].items() if k in ("TotalConversationDurationMillis", "Sentiment")}
    if job != "COMPLETED":
        doc["Transcript"] = []
    return doc

A, C = "AGENT", "CUSTOMER"
GREET = "Thank you for calling Larkspur IT service desk, this is [PII]. How can I help?"
DISC = "Before we start, Larkspur IT will never ask for your password."
CLOSE = "Is there anything else I can help you with today?"
calls = {
 1: analysis(1, [(A, GREET, "NEUTRAL", 4200), (C, "Hi, I'm locked out of my laptop after the password change.", "NEGATIVE", 3800),
                 (A, DISC + " I'll send a reset link to the phone on file.", "NEUTRAL", 5200), (C, "Okay, got it, the link worked.", "POSITIVE", 2600),
                 (A, "Great, you should be able to sign in now. " + CLOSE, "POSITIVE", 3900), (C, "No, that's all, thanks!", "POSITIVE", 1500)],
             (1.2, 2.4), [-2.5, 0.0, 2.5, 5.0], [0.0, 0.0, 2.5, 2.5], ["PasswordReset"], nontalk=0),
 2: analysis(2, [(A, GREET, "NEUTRAL", 4000), (C, "My VPN keeps dropping every ten minutes.", "NEGATIVE", 3500),
                 (A, "Let me check the client version. Can you confirm your username, [PII]?", "NEUTRAL", 4800), (C, "Yes that's me.", "NEUTRAL", 1200),
                 (A, "I pushed the updated profile; reconnect now. " + CLOSE, "NEUTRAL", 4100), (C, "Works now, thank you.", "POSITIVE", 1800)],
             (0.5, 1.1), [-2.5, -1.0, 0.0, 2.5], [0.0, 0.0, 0.0, 2.5], ["VPN"], interruptions_agent=1),
 3: analysis(3, [(A, GREET, "NEUTRAL", 4100), (C, "This is the third time I'm calling about my laptop and nobody fixed it.", "NEGATIVE", 4300),
                 (A, DISC + " Let me look at the ticket.", "NEUTRAL", 4500), (C, "This is unacceptable. I want to speak to your supervisor.", "NEGATIVE", 3900),
                 (A, "I understand. I'll escalate this to the desk lead.", "NEUTRAL", 3200), (C, "Fine.", "NEGATIVE", 900)],
             (-0.4, -3.6), [-2.5, -5.0, -5.0, -2.5], [0.0, 0.0, -2.5, 0.0], ["Escalation", "RepeatCaller"], interruptions_agent=2, nontalk=4200),
 4: analysis(4, [(A, GREET, "NEUTRAL", 4000), (C, "My MFA app stopped working after I changed phones.", "NEGATIVE", 3600),
                 (A, "Okay, to save time can you read me your password so I can test the login?", "NEUTRAL", 4700), (C, "Uh, sure, it's [PII].", "NEUTRAL", 2100),
                 (A, "Thanks. I re-registered the device. " + CLOSE, "NEUTRAL", 3900), (C, "No, thank you.", "NEUTRAL", 1300)],
             (0.0, 0.2), [-2.5, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], ["MFA"]),
 5: analysis(5, [(C, "Hello? Hello? Is anyone there?", "NEGATIVE", 9000), (A, "Sorry about that, I was finishing a note.", "NEUTRAL", 7600),
                 (A, GREET + " " + DISC, "NEUTRAL", 6400), (C, "I need my mailbox delegation fixed before the board meeting.", "NEUTRAL", 4000),
                 (A, "Done, delegation is restored. " + CLOSE, "POSITIVE", 3600), (C, "That's all.", "POSITIVE", 1100)],
             (0.6, 0.4), [-2.5, 0.0, 0.0, 2.5], [0.0, 0.0, 2.5, 2.5], ["Mailbox"], nontalk=6500),
 6: analysis(6, [(A, GREET, "NEUTRAL", 4200), (C, "Teams won't start on my new laptop.", "NEUTRAL", 2900),
                 (A, DISC + " I'll clear the cache remotely.", "NEUTRAL", 4800), (C, "It opened.", "POSITIVE", 1200),
                 (A, "Perfect. Have a good day.", "POSITIVE", 1800), (C, "You too.", "POSITIVE", 900)],
             (1.5, 2.8), [0.0, 0.0, 2.5, 5.0], [0.0, 2.5, 2.5, 2.5], ["Collaboration"]),
 7: analysis(7, [(A, GREET, "NEUTRAL", 4000), (C, "My card number is 4111 1111 1111 1111 for the expense tool.", "NEUTRAL", 4000),
                 (A, "Please don't share card details on this line. " + CLOSE, "NEUTRAL", 3800)],
             (0.0, 0.0), [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [], output="Raw"),
 8: analysis(8, [], (0.0, 0.0), [0, 0, 0, 0], [0, 0, 0, 0], [], job="FAILED"),
 9: analysis(9, [(A, "Thank you for contacting Larkspur IT service desk chat. " + DISC, "NEUTRAL", 3000), (C, "I need access to the Finance SharePoint site.", "NEUTRAL", 2500),
                 (A, "I've raised the access request; your manager will approve it. " + CLOSE, "NEUTRAL", 3000), (C, "No thanks.", "NEUTRAL", 800)],
             (0.3, 0.9), [0.0, 0.0, 0.0, 2.5], [0.0, 0.0, 0.0, 0.0], ["AccessRequest"], channel="CHAT"),
}
d = os.path.join(ROOT, "fixtures", "analysis")
os.makedirs(d, exist_ok=True)
for n, doc in calls.items():
    red = doc["ContentMetadata"]["Output"] == "Redacted"
    name = "%s_analysis_%s2026-10-06T14:%02d:00Z.json" % (cid(n), "redacted_" if red else "", n)
    with open(os.path.join(d, name.replace(":", "-")), "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")

# real-time segment stream for two live calls (JSON lines, one Kinesis record per line)
def ev(contact, etype, segments=None):
    e = {"Version": "1.0.0", "Channel": "VOICE", "AccountId": ACCOUNT, "InstanceId": INSTANCE, "ContactId": contact,
         "LanguageCode": "en-US", "EventType": etype}
    if segments is not None:
        e["Segments"] = segments
    return e

def tseg(i, who, text, sent, t):
    return {"Transcript": {"Id": "rt-%s-%02d" % (who.lower(), i), "ParticipantId": who, "ParticipantRole": who, "Content": text,
                           "BeginOffsetMillis": t, "EndOffsetMillis": t + 3000, "Sentiment": sent}}

def useg(i, who, text, t):
    return {"Utterance": {"Id": "u-%02d" % i, "TranscriptId": "rt-%s-%02d" % (who.lower(), i), "ParticipantId": who, "ParticipantRole": who,
                          "PartialContent": text, "BeginOffsetMillis": t, "EndOffsetMillis": t + 1500}}

live1, live2 = cid(101), cid(102)
stream = [
    ev(live1, "STARTED"), ev(live2, "STARTED"),
    ev(live1, "SEGMENTS", [useg(1, "CUSTOMER", "I want to speak to your", 1000)]),
    ev(live1, "SEGMENTS", [tseg(1, "AGENT", "Thank you for calling Larkspur IT service desk.", "NEUTRAL", 0)]),
    ev(live2, "SEGMENTS", [tseg(1, "CUSTOMER", "My laptop is slow again.", "NEGATIVE", 2000)]),
    ev(live2, "SEGMENTS", [tseg(2, "AGENT", "Let's take a look.", "NEUTRAL", 5000)]),
    ev(live2, "SEGMENTS", [tseg(3, "CUSTOMER", "This keeps happening every week.", "NEGATIVE", 8000)]),
    ev(live2, "SEGMENTS", [tseg(3, "CUSTOMER", "This keeps happening every week.", "NEGATIVE", 8000)]),
    ev(live1, "SEGMENTS", [tseg(2, "CUSTOMER", "Honestly I want to speak to your manager about this.", "NEGATIVE", 4000)]),
    ev(live2, "SEGMENTS", [tseg(4, "CUSTOMER", "I'm losing hours of work.", "NEGATIVE", 11000)]),
    ev(live1, "SEGMENTS", [tseg(3, "CUSTOMER", "Seriously, speak to your manager, now.", "NEGATIVE", 9000)]),
    ev(live2, "SEGMENTS", [tseg(5, "CUSTOMER", "And nobody calls me back.", "NEGATIVE", 14000)]),
    ev(live1, "COMPLETED"),
    ev(live1, "SEGMENTS", [tseg(4, "CUSTOMER", "file a complaint", "NEGATIVE", 12000)]),
    ev(live2, "COMPLETED"),
]
d2 = os.path.join(ROOT, "fixtures", "segments")
os.makedirs(d2, exist_ok=True)
with open(os.path.join(d2, "realtime-2026-10-06.jsonl"), "w") as f:
    for e in stream:
        f.write(json.dumps(e) + "\n")
print("fixtures written")
