# Reference: connect/w3-t1

Root cause: CHG0031877 moved SBCE-B's media interface to the voice DMZ VLAN (ip 10.20.8.15)
and dropped the `public-ip` (NAT) setting. The SBCE now advertises `c=IN IP4 10.20.8.15` in
the SDP it sends to Voice Connector: in the INVITE offer for outbound calls and in the 200 OK
answer for inbound calls. Voice Connector sends RTP to the address in that SDP, which is not
routable on the internet, so the LFG user hears nothing. The SBCE's own RTP leaves through the
static NAT (198.51.100.11) and reaches Voice Connector, so the far end hears the LFG user.

Evidence:
- `make audit` (or reading the SDP): exactly the three dead-air calls (0c8e5b71..., c2a4e6f8...,
  9b7d5f3e...) carry c=10.20.8.15; all go through SBCE-B; the three good calls go through SBCE-A.
- Media metrics: for SBCE-B calls VC sends a normal 50 pps (vc2cust_rtp_packets) and receives
  normally (cust2vc), but the SBC's RTCP receiver reports say 100% lost; MOS 1.0.
- CloudWatch: MOSBetweenVcAndCustomer falls from 4.3 to about 2.65 on 2026-10-02 (half the
  calls are perfect, half are 1.0) and stays there; no 5xx, no throttles.
- Diff: `-public-ip = 198.51.100.11`; NAT table: 198.51.100.11 <-> 10.20.8.15 udp/35000-40000 exists.
- Change test: ext 4410 -> ext 4418 never crossed the trunk, so it could not catch it.
- Intermittency: origination routes SBCE-A/B at priority 1, weight 50/50; outbound users are
  homed on either SBCE.

Red herring: telephone-event 127 (SBCE) vs 101 (VC). RFC 4733 payload types are dynamic and
each side sends using the PT the other side declared; the mismatch is present on every call,
including the good ones, and DTMF works. Do not change it.

Fix: `public-ip = 198.51.100.11` under `[media-interface trunk-vc-media]` in
`config/sbc/ashburn-sbce-b.conf` (or back out to 10.20.4.22 with its public-ip). `make replay`
then reports 0 one-way calls.

Prevention: PSTN test calls through every SBC on every change touching interfaces; auditSdp in
CI against rendered profiles; per-SBC MOS and packet-loss alarms from the media metric logs;
synthetic calls per origination route.
