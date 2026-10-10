# Constraints and decisions already made

1. Agent waves: Wave 1 Pune offshore team (120 agents) on Connect by 2026-12-07; Wave 2
   onshore general support (150) by 2027-01-25; Wave 3 VIP desk, password reset, Chicago,
   Toronto, on-call hotline by 2027-03-08; Wave 4 London (Genesys) by 2027-05-17.
2. Change freezes: 2026-12-18 to 2027-01-04 (year end) and the last 5 business days of each
   quarter (finance close). No porting events inside a freeze.
3. The help desk number 1-800-555-0142 must never be down; maximum tolerated degradation is 15
   minutes during an announced window, outside 06:00-20:00 ET.
4. During coexistence, an agent on either platform must be able to transfer a caller to the
   other platform with the employee ID and the ServiceNow incident number available to the
   receiving agent.
5. Budget: no new carrier contracts beyond the Voice Connector trunk; no third-party SIP
   interconnect into Connect (AWS has not approved one, and the account team says a Voice
   Connector-into-Connect bridge needs an architecture review they do not expect to grant).
6. Security wants call recordings and analytics for all help desk calls from Wave 1, including
   calls still handled on Avaya (audit finding AF-2026-14).
7. The Pune NOC runs operations 24x7; Monterrey covers 07:00-19:00 CT; the onshore telephony
   team is three people.
