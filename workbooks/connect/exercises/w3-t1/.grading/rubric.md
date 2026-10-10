# Rubric: connect/w3-t1 Dead air on the new SIP trunk
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: SBCE-B's media interface moved to 10.20.8.15 by CHG0031877 without a public (NAT) media address, so its SDP (INVITE offer on outbound, 200 OK answer on inbound) carries c=IN IP4 10.20.8.15; Voice Connector sends RTP to that unroutable address, so LFG users hear nothing while their outbound RTP (sourced via the static NAT) still reaches the far end; calls via SBCE-A (50/50 origination weight) work, hence "redial usually works". Partial (10-15): "NAT problem on SBC-B" without the SDP mechanism or the direction of the failure. Zero: blames DTMF, codecs, Voice Connector or the carrier. |
| 3 | Evidence | 20 | Full: at least three quoted pieces: the c= line from failing vs working calls (SIP logs or ladders), media metrics showing VC sending packets while the SBC reports ~100% loss / MOS 1.0 only for SBCE-B calls, the change diff removing public-ip, the NAT table showing 10.20.8.15 maps to 198.51.100.11, CloudWatch MOS drop starting 2026-10-02. Explains the change test passed because ext-to-ext calls never left the LAN. Partial: one or two pieces. |
| 4 | Red herring handled | 5 | Rules out INC0094410: RFC 4733 telephone-event payload types are dynamic and negotiated per direction; the same 127/101 pair is present on working calls, DTMF works, and the PT has been unchanged since July. Does not "align to 101". |
| 5 | Fix quality | 10 | Adds public-ip = 198.51.100.11 to SBCE-B's media interface (or performs the documented backout to 10.20.4.22 with its public-ip) and nothing else; auditSdp clean, readable, line numbers right. |
| 6 | Prevention / production | 10 | Concrete: test plans that place a PSTN call through each SBC (not ext-to-ext), auditSdp in CI over rendered profiles, per-SBC MOS/packet-loss alarms (media metric logs, MOSBetweenVcAndCustomer), SIP OPTIONS plus synthetic calls per origination route, change review for media interfaces. Partial: generic "monitor more". |
Total: 100
