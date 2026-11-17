# Rubric: connect/w4-c2 Migration program plan
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Wave strategy | 20 | Full: waves ordered by risk and value with explicit reasons; respects the Avaya/Five9/Cisco dates and the blackouts from inputs/; entry/exit criteria per wave; a pilot that proves porting. Partial: sensible waves without dates or criteria. Zero: big-bang without justification. |
| 3 | Coexistence and telephony | 15 | Full: names a coexistence pattern (e.g. the AWS Avaya guidance options), how transfers and context cross platforms without assuming undocumented UUI pass-through into Connect, porting lead times and LOAs, agents never split across platforms in a shift. Partial: coexistence mentioned, mechanics vague. |
| 4 | Validation and testing | 15 | Full: legacy-vs-Connect path suites (incl. holidays/DST), integration, UAT, load at >= 1.2x peak, accessibility, synthetic calls, parallel run, each with an owner and a gate. Partial: a list without gates. |
| 5 | Cutover and rollback | 20 | Full: T-minus runbook with go/no-go points; rollback triggers, decision owner, per-layer technical rollback, and the honest point that a completed port is not quickly reversible (rollback by routing, not re-porting). Partial: rollback = "port back". Zero: none. |
| 6 | Offshore delivery model | 15 | Full: RACI across onshore/offshore/nearshore/client/carrier, overlap hours, review cadence, definition of done, migration factory with rationalisation. Partial: RACI only. |
| 7 | Hypercare, KT, decommission, risks | 15 | Full: hypercare length, KPIs and exit criteria, KT plan, recording/data retention before decommission, top risks with owners and decisions recorded. Partial: generic. |
Total: 100
