# Reference: modernize/x-2

Model answer: `.grading/solution/DESIGN.md`. The traps a strong answer catches:

- Dropping 2.x strands three consumers (ClaimDesk until EAP 8, AgentPortal frozen until July, the Boot 2.7 batch).
- AgentPortal's `[2.0,)` range would pull 3.0 on its next unrelated build and fail at deploy on EAP 7.4.
- The DDL rides inside the library and runs from every consumer's Flyway at startup against a shared schema:
  an irreversible online change on 410 M rows triggered by whichever app deploys first. Split it out, make it
  additive, run it once in a DBA window, and disable commons-schema migrations in consumers.
- The REST/JSON contract and the SQL extracts are consumers too, with no Java dependency at all.
- Parallel change: publish javax 2.15 and jakarta 3.0 from one source, with a support end date tied to the last
  consumer's plan, then contract.
