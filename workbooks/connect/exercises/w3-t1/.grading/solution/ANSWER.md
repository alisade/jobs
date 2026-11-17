# ANSWER: connect/w3-t1 Dead air on the new SIP trunk

## Approach

Listed the six calls in homer-ladders.txt by outcome and SBC: all three dead-air calls use
SBCE-B (198.51.100.11), all good ones SBCE-A. Compared SDP bodies in vc-sip-messages.jsonl,
then media metrics, CloudWatch, the change diff and the NAT table. Checked the DTMF ticket
against the good calls.

## Root cause

CHG0031877 moved SBCE-B's media interface to 10.20.8.15 and removed `public-ip`, so SBCE-B
advertises `c=IN IP4 10.20.8.15` (INVITE offer outbound, 200 OK answer inbound), e.g.
call 0c8e5b71... line 4 of the SDP. Voice Connector sends RTP to that private address, so LFG
users hear nothing; SBCE-B's own RTP goes out via the static NAT 198.51.100.11, so the far end
hears them. Media metrics for SBCE-B calls: vc2cust_rtp_packets 450/min but
cust_reported_fraction_lost_pct 100, mos_vc_to_customer 1.0; SBCE-A calls 0.1% and 4.3.
CloudWatch MOS avg 4.31 -> 2.67 from 2026-10-02 (half the calls at 1.0). The change test was
extension to extension on the LAN and never crossed the trunk. Redial works because origination
splits 50/50 across SBCE-A and B. INC0094410 is unrelated: RFC 4733 payload types are dynamic
per direction, the same 127/101 pair appears on the working calls, and DTMF works.

## Fix

Added `public-ip = 198.51.100.11` to SBCE-B's media interface (matches FW-2219 NAT). make audit
over the bundle flags exactly the three failing calls; make replay: 0 / 200 one-way; make test passes.

## Trade-offs / what I would do in production

Change test plans must include PSTN calls through each SBC; run auditSdp in CI on rendered
profiles; alarm per SBC on MOS/packet loss from the media metric logs; synthetic calls per
origination route; leave the DTMF payload types alone.
