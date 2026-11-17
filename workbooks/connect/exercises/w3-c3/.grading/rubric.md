# Rubric: connect/w3-c3 Hybrid coexistence and number porting cutover plan
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Inventory analysis | 10 | Full: separate port tickets per carrier and country, numbers that stay (back-office, reception) excluded, special cases called out (UK lead time, Chime SDK hotline via support case, Five9 caller ID number), critical path identified. Partial: a flat list of numbers. |
| 3 | Coexistence architecture is real | 20 | Full: uses only documented patterns: PSTN forwarding/transfer between platforms, forward-then-port, Voice Connector only for PBX-to-PSTN, no native BYOC into Connect and no Voice Connector-into-Connect bridge without AWS review; SIPREC to a conversational analytics connector for Avaya call analytics (with AmznConnectAgentUserId and quota requests). Clear primary platform per number per wave. Partial: sound but one undocumented assumption (e.g. "SIP trunk from Avaya to Connect"). Zero: architecture depends on an invented Connect SIP trunk. |
| 4 | Context passing | 10 | Full: recognises UUI/X- headers do not reach Connect over the PSTN; proposes a correlation mechanism (DNIS pool / ANI+DNIS data dip with TTL, or API/CTI) in both directions with a no-match fallback. Partial: one direction only. |
| 5 | Porting plan grounded in the docs | 20 | Full: support case per carrier+country; US/CA requests no earlier than 30 days before, typically 2-4 weeks, international 2-6 months; LOA/CSR accuracy as the main risk (rejection resets); test on a temporary claimed number first; dates avoid freezes and quarter close; ACGR needs ported numbers. Partial: correct sequencing, few specifics. |
| 6 | Cutover runbook and parallel run | 15 | Full: dated runbook for one port with owners, go/no-go gates, test matrix from multiple carriers/mobile, monitoring signals, hypercare; parallel run with measurable exit criteria. Partial: list of steps without gates or criteria. |
| 7 | Rollback plan | 15 | Full: distinguishes before / during / after the port; knows a port cannot be cancelled once at the new RespOrg, reschedule needs 5 business days, and reverting requires a new LOA (port away), so post-port rollback is forward-back to legacy DIDs kept live for a defined period. Partial: "port back if it fails". Zero: no rollback. |
| 8 | Risks, RACI, comms and ANSWER.md | 10 | Full: top risks with owners; RACI covering the offshore NOC, carriers and AWS; ANSWER.md lists key decisions and rejected alternatives. Partial: generic. |
Total: 100
