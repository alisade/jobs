# connect/w3-t1 - Dead air on the new SIP trunk

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 3 (Mon: SIP/SDP/RTP, NAT and one-way audio, DTMF; Thu: Voice Connector logging and metrics)

## Symptom

Since last week, some Larkspur back-office users on Avaya phones hear nothing on calls
through the new Amazon Chime SDK Voice Connector trunk, while the other party hears them fine.
It happens on inbound and outbound calls; a redial usually works. The Voice Connector
dashboard shows no 5xx responses and no throttling, but average MOS dropped. The Pune NOC
suspects a DTMF payload type mismatch that has been open as a separate ticket. Read
`incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and the on-call notes |
| `incident/homer-ladders.txt` | sngrep/Homer style ladders for six calls (decrypted on the SBCE) |
| `incident/vc-sip-messages.jsonl` | Voice Connector SIP message logs (full SIP text per message) |
| `incident/vc-media-metrics.jsonl` | Voice Connector media metric logs, as exported by LFG's log shipper (field names renamed) |
| `incident/cloudwatch-metrics.txt` | daily `AWS/ChimeVoiceConnector` metrics |
| `incident/CHG0031877.diff`, `incident/firewall-voice-dmz.txt`, `incident/INC0094410.txt` | change record, NAT table, the DTMF ticket |
| `config/sbc/*.conf` | simplified exports of the three Avaya SBCE trunk profiles (edit these) |
| `src/sbc-sim.ts` | how the SBCE builds its SDP from the profile (works as shipped) |
| `src/replay.ts` | replays 200 calls through the current profiles, following the media (works as shipped) |
| `src/sdp-audit.ts` | the SDP audit you write |

## Your task

1. Find the root cause from the evidence: which calls fail, what they have in common, the
   exact SDP line that breaks media, and why the change's test call passed.
2. Implement `auditSdp(sdp)` in `src/sdp-audit.ts` so the team can run it in CI against
   every SBC profile and in the NOC against SIP logs. Codes (line = 1-based line in the body):
   - `PRIVATE_CONNECTION_ADDRESS` (error) on any `c=IN IP4` in 10/8, 172.16/12, 192.168/16,
     100.64/10 (CGNAT), 127/8 or 169.254/16, session or media level;
   - `NOT_SRTP` (error) on an `m=audio` line using `RTP/AVP` (the trunk requires encryption);
   - `MISSING_CRYPTO` (error) on an `m=audio` `RTP/SAVP` line with no `a=crypto`;
   - `NO_TELEPHONE_EVENT` (warning) on an `m=audio` line with no `telephone-event` rtpmap;
   - `MISSING_CONNECTION` (error) on an `m=audio` line when there is no `c=` at either level.
3. Fix the SBC profile with the smallest change that restores two-way audio. Do not change
   unrelated settings on any SBCE.
4. Verify: `make test`, `make audit` (bundle findings) and `make replay` (no one-way calls).
5. Write `ANSWER.md`: Approach, Root cause (with evidence: commands, log lines, SDP lines,
   metrics), Fix and verification, Trade-offs / production follow-ups. Say explicitly why
   the DTMF ticket is or is not related.

## Acceptance criteria (what the grader checks)

- `auditSdp` returns the right findings for crafted SDPs and flags exactly the failing calls
  in the bundle.
- Every SBCE profile renders an SDP with a public media address; replay has zero one-way calls.
- Unrelated SBCE settings unchanged (guard tests).
- The root cause in `ANSWER.md` names the mechanism and is backed by evidence. A fixed config
  with a hand-waved explanation does not pass.

## How to run

```bash
make setup     # links the toolchain and writes incident/
make audit     # your auditSdp over every SDP in incident/vc-sip-messages.jsonl
make replay    # 200 calls through the current SBC profiles
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w3-t1
make clean
```

Useful: `grep -h '"call_id"' incident/vc-sip-messages.jsonl | head -1 | python3 -m json.tool`,
`jq -r 'select(.cust_reported_fraction_lost_pct > 50) | .call_id' incident/vc-media-metrics.jsonl | sort -u`.
