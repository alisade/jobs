// Generates the incident bundle in incident/ (deterministic). The bundle is evidence of the
// incident: it is rendered from the SBC configuration AS IT WAS during the incident (embedded
// below), not from config/sbc/, so fixing the config does not change the evidence.
// Usage: node scripts/make-bundle.js [outDir]
const fs = require("fs");
const path = require("path");

const out = path.resolve(process.argv[2] || path.join(__dirname, "../incident"));
fs.mkdirSync(out, { recursive: true });

const VC_ID = "bq9x2rkd7m3fzv8wtle4hy";
const VC_HOST = `${VC_ID}.voiceconnector.chime.aws`;
const VC_MEDIA = "3.80.16.42";
const VC_SIG = "3.80.16.17";
const SBC = {
  "ashburn-sbce-a": { sig: "198.51.100.10", lan: "10.20.4.21", media: "198.51.100.10" },
  "ashburn-sbce-b": { sig: "198.51.100.11", lan: "10.20.4.22", media: "10.20.8.15" }, // incident state
};
const KEY = "WVNfX19zZW1jdGwgKCkgewkyMjA7fQp9CnVubGVz";
const VCKEY = "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo3NjU0";
const CRLF = "\r\n";

function sbcSdp(name, sess, port) {
  const s = SBC[name];
  return [
    "v=0", `o=SBCE ${sess} 1 IN IP4 ${s.sig}`, "s=-", `c=IN IP4 ${s.media}`, "t=0 0",
    `m=audio ${port} RTP/SAVP 0 8 127`, "a=rtpmap:0 PCMU/8000", "a=rtpmap:8 PCMA/8000",
    "a=rtpmap:127 telephone-event/8000", "a=fmtp:127 0-15", "a=ptime:20",
    `a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:${KEY}`, "a=sendrecv",
  ].join(CRLF) + CRLF;
}
function vcSdp(sess, port) {
  return [
    "v=0", `o=- ${sess} 1 IN IP4 ${VC_MEDIA}`, "s=-", `c=IN IP4 ${VC_MEDIA}`, "t=0 0",
    `m=audio ${port} RTP/SAVP 0 101`, "a=rtpmap:0 PCMU/8000", "a=rtpmap:101 telephone-event/8000",
    "a=fmtp:101 0-16", "a=ptime:20", `a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:${VCKEY}`, "a=sendrecv",
  ].join(CRLF) + CRLF;
}
function sip(start, headers, body) {
  const h = [...headers];
  h.push(`Content-Length: ${body ? Buffer.byteLength(body) : 0}`);
  if (body) h.push("Content-Type: application/sdp");
  return [start, ...h].join(CRLF) + CRLF + CRLF + (body || "");
}

// calls: direction out = Avaya user calls PSTN (SBC -> VC); in = PSTN calls Avaya DID (VC -> SBC)
const calls = [
  { id: "7f3c19a2e4d84b0e9a61c2d5f0b8e113", sbc: "ashburn-sbce-a", dir: "out", t: "2026-10-08T13:58:02.114Z", from: "+12125554410", to: "+16175550188", dur: 312, ok: true },
  { id: "0c8e5b71d2a94f6e8b3a1d9c7e5f2a40", sbc: "ashburn-sbce-b", dir: "out", t: "2026-10-08T14:02:11.120Z", from: "+12125554418", to: "+17185550102", dur: 9, ok: false },
  { id: "c2a4e6f8b0d24c1e9f7a5b3d1c0e8a26", sbc: "ashburn-sbce-b", dir: "in", t: "2026-10-08T14:05:47.902Z", from: "+13125550177", to: "+12125554400", dur: 14, ok: false },
  { id: "5e1d7c3b9a8f4e2d6c0b1a9f8e7d6c55", sbc: "ashburn-sbce-a", dir: "in", t: "2026-10-08T14:07:30.004Z", from: "+14155550133", to: "+12125554400", dur: 251, ok: true, dtmf: "2" },
  { id: "9b7d5f3e1c2a4b6d8f0e1a3c5e7b9d01", sbc: "ashburn-sbce-b", dir: "out", t: "2026-10-08T14:11:05.660Z", from: "+12125554436", to: "+18005550142", dur: 21, ok: false },
  { id: "e4c6a8b0d2f14e3c5a7b9d1f3e5c7a92", sbc: "ashburn-sbce-a", dir: "out", t: "2026-10-08T14:12:44.318Z", from: "+12125554421", to: "+18005550142", dur: 188, ok: true, dtmf: "1" },
];

const addMs = (iso, ms) => new Date(Date.parse(iso) + ms).toISOString();
const lines = [];
const ladders = [];
let cseq = 101;
for (const c of calls) {
  const s = SBC[c.sbc];
  const sess = String(Date.parse(c.t) % 100000000);
  const sbcPort = 35000 + (parseInt(c.id.slice(0, 4), 16) % 2500) * 2;
  const vcPort = 17000 + (parseInt(c.id.slice(4, 8), 16) % 4000) * 2;
  const tag1 = c.id.slice(0, 8), tag2 = c.id.slice(24);
  const callId = `${c.id}@${s.lan}`;
  const msgs = [];
  if (c.dir === "out") {
    const via = `Via: SIP/2.0/TLS ${s.sig}:5061;branch=z9hG4bK${c.id.slice(8, 16)};rport`;
    const from = `From: <sip:${c.from}@${s.sig}>;tag=${tag1}`;
    const to = `To: <sip:${c.to}@${VC_HOST}>`;
    const base = [via, `Max-Forwards: 69`, from];
    msgs.push([0, "SBC->VC", "INVITE (SDP)", sip(`INVITE sip:${c.to}@${VC_HOST}:5061;transport=tls SIP/2.0`, [...base, to, `Call-ID: ${callId}`, `CSeq: ${cseq} INVITE`, `Contact: <sip:${c.from}@${s.sig}:5061;transport=tls>`, "User-Agent: Avaya SBCE", "Allow: INVITE, ACK, BYE, CANCEL, OPTIONS"], sbcSdp(c.sbc, sess, sbcPort))]);
    msgs.push([60, "VC->SBC", "100 Trying", sip("SIP/2.0 100 Trying", [via, from, to, `Call-ID: ${callId}`, `CSeq: ${cseq} INVITE`])]);
    msgs.push([2900, "VC->SBC", "183 Session Progress (SDP)", sip("SIP/2.0 183 Session Progress", [via, from, `${to};tag=${tag2}`, `Call-ID: ${callId}`, `CSeq: ${cseq} INVITE`], vcSdp(sess, vcPort))]);
    msgs.push([7400, "VC->SBC", "200 OK (SDP)", sip("SIP/2.0 200 OK", [via, from, `${to};tag=${tag2}`, `Call-ID: ${callId}`, `CSeq: ${cseq} INVITE`, `Contact: <sip:${c.to}@${VC_SIG}:5061;transport=tls>`], vcSdp(sess, vcPort))]);
    msgs.push([7460, "SBC->VC", "ACK", sip(`ACK sip:${c.to}@${VC_SIG}:5061;transport=tls SIP/2.0`, [via.replace(c.id.slice(8, 16), c.id.slice(16, 24)), from, `${to};tag=${tag2}`, `Call-ID: ${callId}`, `CSeq: ${cseq} ACK`])]);
    msgs.push([7400 + c.dur * 1000, "SBC->VC", "BYE", sip(`BYE sip:${c.to}@${VC_SIG}:5061;transport=tls SIP/2.0`, [via, from, `${to};tag=${tag2}`, `Call-ID: ${callId}`, `CSeq: ${cseq + 1} BYE`, c.ok ? "Reason: Q.850;cause=16;text=\"Normal call clearing\"" : "Reason: Q.850;cause=16;text=\"Normal call clearing\""])]);
    msgs.push([7400 + c.dur * 1000 + 40, "VC->SBC", "200 OK", sip("SIP/2.0 200 OK", [via, from, `${to};tag=${tag2}`, `Call-ID: ${callId}`, `CSeq: ${cseq + 1} BYE`])]);
  } else {
    const via = `Via: SIP/2.0/TLS ${VC_SIG}:5061;branch=z9hG4bK${c.id.slice(8, 16)}`;
    const from = `From: <sip:${c.from}@${VC_HOST}>;tag=${tag2}`;
    const to = `To: <sip:${c.to}@${s.sig}>`;
    msgs.push([0, "VC->SBC", "INVITE (SDP)", sip(`INVITE sip:${c.to}@${s.sig}:5061;transport=tls SIP/2.0`, [via, "Max-Forwards: 69", from, to, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq} INVITE`, `Contact: <sip:${c.from}@${VC_SIG}:5061;transport=tls>`], vcSdp(sess, vcPort))]);
    msgs.push([40, "SBC->VC", "100 Trying", sip("SIP/2.0 100 Trying", [via, from, to, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq} INVITE`])]);
    msgs.push([1800, "SBC->VC", "180 Ringing", sip("SIP/2.0 180 Ringing", [via, from, `${to};tag=${tag1}`, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq} INVITE`])]);
    msgs.push([5100, "SBC->VC", "200 OK (SDP)", sip("SIP/2.0 200 OK", [via, from, `${to};tag=${tag1}`, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq} INVITE`, `Contact: <sip:${c.to}@${s.sig}:5061;transport=tls>`, "Server: Avaya SBCE"], sbcSdp(c.sbc, sess, sbcPort))]);
    msgs.push([5150, "VC->SBC", "ACK", sip(`ACK sip:${c.to}@${s.sig}:5061;transport=tls SIP/2.0`, [via, from, `${to};tag=${tag1}`, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq} ACK`])]);
    msgs.push([5100 + c.dur * 1000, "VC->SBC", "BYE", sip(`BYE sip:${c.to}@${s.sig}:5061;transport=tls SIP/2.0`, [via, from, `${to};tag=${tag1}`, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq + 1} BYE`])]);
    msgs.push([5100 + c.dur * 1000 + 35, "SBC->VC", "200 OK", sip("SIP/2.0 200 OK", [via, from, `${to};tag=${tag1}`, `Call-ID: ${c.id}@${VC_SIG}`, `CSeq: ${cseq + 1} BYE`])]);
  }
  cseq += 7;
  const ladder = [
    `Call-ID: ${c.dir === "out" ? callId : c.id + "@" + VC_SIG}   ${c.dir === "out" ? "OUTBOUND (Avaya -> PSTN)" : "INBOUND (PSTN -> Avaya)"}`,
    `From: ${c.from}   To: ${c.to}   SBC: ${c.sbc} (${s.sig})   Voice Connector: ${VC_HOST}`,
    `${"".padEnd(26)}${c.sbc.padEnd(24)}voiceconnector`,
    `${"".padEnd(26)}${s.sig.padEnd(24)}${VC_SIG}`,
  ];
  for (const [ms, dir, label, text] of msgs) {
    const ts = addMs(c.t, ms).replace("T", " ").replace("Z", "");
    const arrow = dir === "SBC->VC" ? `|---- ${label} ${"-".repeat(Math.max(1, 24 - label.length))}>|` : `|<--- ${label} ${"-".repeat(Math.max(1, 24 - label.length))}-|`;
    ladder.push(`${ts}  ${arrow}`);
    lines.push(JSON.stringify({ voice_connector_id: VC_ID, aws_region: "us-east-1", event_timestamp: addMs(c.t, ms), call_id: c.id, sip_message: text }));
  }
  if (c.dtmf) ladder.push(`  (RTP telephone-event digit ${c.dtmf} observed in both directions; IVR menu selection worked)`);
  ladder.push(`  call length ${c.dur} s` + (c.ok ? "" : "   <- user reported they could not hear the other party"));
  ladders.push(ladder.join("\n"));
}

fs.writeFileSync(path.join(out, "vc-sip-messages.jsonl"), lines.join("\n") + "\n");
fs.writeFileSync(path.join(out, "homer-ladders.txt"),
  "Homer / sngrep style call flows exported from the SBCE trace (HEP) for 2026-10-08 14:00-14:15 UTC.\n" +
  "Signaling is TLS: these are decrypted on the SBCE before export. Full messages: vc-sip-messages.jsonl.\n\n" +
  ladders.join("\n\n" + "=".repeat(96) + "\n\n") + "\n");

// Media metric log export (the log shipper renames the Voice Connector media metric fields).
const media = [];
for (const c of calls) {
  const s = SBC[c.sbc];
  const minutes = Math.max(1, Math.ceil(c.dur / 60));
  for (let m = 0; m < minutes; m++) {
    const secs = Math.min(60, c.dur - m * 60);
    const pk = secs * 50;
    media.push({
      ts: addMs(c.t, 8000 + m * 60000), voice_connector_id: VC_ID, call_id: c.id, sbc_signaling_ip: s.sig,
      cust2vc_rtp_packets: pk, vc2cust_rtp_packets: pk,
      cust2vc_packets_lost: c.ok ? Math.floor(pk * 0.001) : 0,
      cust2vc_jitter_ms: c.ok ? 3.1 : 2.8,
      vc2cust_rtcp_rr_received: c.ok ? Math.ceil(secs / 5) : Math.ceil(secs / 5),
      cust_reported_fraction_lost_pct: c.ok ? 0.1 : 100.0,
      mos_vc_to_customer: c.ok ? 4.3 : 1.0,
    });
  }
}
fs.writeFileSync(path.join(out, "vc-media-metrics.jsonl"), media.map((x) => JSON.stringify(x)).join("\n") + "\n");

fs.writeFileSync(path.join(out, "PAGE.txt"), `INC0094431  P2  "Calls through the new SIP trunk: people cannot hear the other side"
Opened 2026-10-08 14:20 UTC by the IT service desk (Avaya back-office users, Midtown floors 8-12)

Since Friday some calls are "dead air" for our people: the person they called (or who called
them) can hear them fine, but they hear nothing. Hanging up and redialing usually works.
Roughly half of the complaints are outbound, half are inbound to the main back-office number.
The help desk Connect number (+1 800 555 0142) is affected when dialed from Avaya phones.

Telephony on-call notes (Ravi K., Pune NOC):
- Voice Connector dashboard shows no 5xx, no throttles, calls answer normally.
- MOSBetweenVcAndCustomer average dropped from 4.3 to ~2.6 since Thursday night.
- INC0094410 (open since Tuesday) says DTMF payload types do not match (127 vs 101). Could
  this be it? Vendor suggested aligning telephone-event to 101 on all SBCEs.
- Change calendar: CHG0031877 (Thu 2026-10-01 22:00 ET) "Move SBCE-B media interface to the new
  voice DMZ VLAN 10.20.8.0/24" - closed successful, test call passed (internal extension).

Evidence exported for you: homer-ladders.txt, vc-sip-messages.jsonl (CloudWatch log group
/aws/ChimeVoiceConnectorSipMessages/${VC_ID}), vc-media-metrics.jsonl (Splunk export of
/aws/ChimeVoiceConnectorLogs/${VC_ID}, fields renamed by the shipper), cloudwatch-metrics.txt,
CHG0031877.diff, firewall-voice-dmz.txt, INC0094410.txt.
`);

fs.writeFileSync(path.join(out, "CHG0031877.diff"), `--- sbce-ash-b trunk profile (before CHG0031877)
+++ sbce-ash-b trunk profile (after CHG0031877)
@@ [media-interface trunk-vc-media] @@
-ip = 10.20.4.22
-public-ip = 198.51.100.11
+ip = 10.20.8.15
 rtp-port-range = 35000-40000
@@ change record @@
 Summary: Move SBCE-B media interface to the new voice DMZ VLAN 10.20.8.0/24 (firewall team
          owns the static NAT, see FW-2219). Implementer: contractor (night shift).
 Test plan: internal test call ext 4410 -> ext 4418 via SBCE-B. Result: PASS.
 Backout: restore interface on 10.20.4.22.
`);

fs.writeFileSync(path.join(out, "firewall-voice-dmz.txt"), `FW-2219  voice DMZ (palo-ash-edge-01)  exported 2026-10-08 14:30 UTC

static-nat  198.51.100.10  <->  10.20.4.21    sbce-ash-a  signaling+media   (unchanged)
static-nat  198.51.100.11  <->  10.20.4.22    sbce-ash-b  signaling         (unchanged)
static-nat  198.51.100.11  <->  10.20.8.15    sbce-ash-b  media udp/35000-40000   (added 2026-10-01, FW-2219)

rule 410 allow  src 3.80.16.0/23, 99.77.253.0/24   dst 198.51.100.10-11  tcp/5061           tls-sip
rule 411 allow  src 3.80.16.0/23, 99.77.253.0/24   dst 198.51.100.10-11  udp/35000-40000    srtp
rule 412 allow  src 10.20.4.21-22, 10.20.8.15      dst any               udp/5000-65000     srtp out
hit counts (24h): rule 410: 18,442   rule 411: 61,903,227   rule 412: 120,334,018
`);

fs.writeFileSync(path.join(out, "cloudwatch-metrics.txt"), `Namespace AWS/ChimeVoiceConnector  VoiceConnectorId ${VC_ID}  (hourly, 2026-09-30 .. 2026-10-08)

date        Inbound   Outbound  Sip5xxCodes  Throttles  MOSBetweenVcAndCustomer(avg)  CustomerToVcJitter(avg ms)
2026-09-30    1,904     2,311          0          0             4.31                       3.0
2026-10-01    1,876     2,290          0          0             4.30                       3.1
2026-10-02    1,911     2,402          0          0             2.67                       3.0
2026-10-05    1,850     2,250          0          0             2.63                       2.9
2026-10-06    1,899     2,377          0          0             2.65                       3.0
2026-10-07    1,868     2,301          0          0             2.64                       3.1
2026-10-08    1,120     1,402          0          0             2.66                       3.0
`);

fs.writeFileSync(path.join(out, "INC0094410.txt"), `INC0094410  P4  "DTMF payload type mismatch on the Voice Connector trunk"  opened 2026-10-06
Observation (Pune NOC): SBCE offers telephone-event as payload type 127; Voice Connector answers
with telephone-event payload type 101. "This mismatch could break DTMF or audio."
Vendor (VAR) suggestion: set telephone-event-pt = 101 on all SBCEs during the next window.
Notes: IVR menu selections through the trunk (Connect help desk menu, voicemail PINs) are
working per the service desk; no DTMF complaints received. Payload type 127 has been in the
profile since the trunk went live in July.
`);
console.log(`bundle written to ${out}`);
