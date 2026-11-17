# Release calendar and constraints (2027 H1)

- Production windows Tue/Thu 20:00-23:00 ET. Freezes: last 5 and first 3 business days of each month,
  and 2027-03-22 to 2027-04-02 (regulatory filing).
- ClaimDesk: JDK 21 on EAP 7.4 in February, EAP 8 / Jakarta in April-May (pod plan).
- PolicyHub: wants commons 3.0 by end of March to drop the transformer.
- AgentPortal: frozen until July except security fixes.
- AUDIT_EVENT: online DDL on the 410 M row table needs a DBA window (Sunday 02:00-06:00) and is
  irreversible without a restore.
- Every consumer must stay deployable with its current version until it upgrades.
