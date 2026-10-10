# Reference: connect/w3-c3

Model answer: `.grading/solution/DESIGN.md` and `.grading/solution/ANSWER.md`.

What great looks like:

- Treats porting as a project with hard external lead times: one ticket per carrier and
  country, the 30-day US/CA submission window, 2-4 weeks US/CA vs 2-6 months elsewhere (so the
  UK ticket starts now), LOA/CSR accuracy, temporary-number testing, freeze calendar.
- Keeps the architecture inside what AWS documents: forward legacy numbers to Connect-claimed
  numbers until conversion, then port; transfers between platforms over the PSTN; Voice
  Connector only as the Avaya back-office PBX trunk; no BYOC into Connect; SIPREC to a
  conversational analytics connector for analytics on calls still on Avaya.
- Solves context passing without SIP headers (not documented for Connect over the PSTN).
- Rollback that is honest about porting: before (vector percentage), during (no cancel after
  the RespOrg move; 5 business days to reschedule), after (forward-back; a revert is a new
  port with a new LOA).
- Remembers ACGR needs ported numbers, quotas (concurrent calls default 10, analytics
  connectors default 0), and the Chime SDK hotline's separate port path.

Common misses: an invented "Connect SIP trunk" from the Avaya SBC; porting the 1-800 number in
Wave 1 with no forward phase; ignoring the UK lead time; rollback = "port it back tomorrow".
