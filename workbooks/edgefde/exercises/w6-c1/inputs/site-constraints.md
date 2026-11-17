# Site constraints (from the security questionnaire and the plant engineering standard)

| Area | Constraint |
|---|---|
| Network | OT level 2 has no internet. Outbound only via the level 3.5 proxy (TLS inspection, allow-list). |
| Data residency | Raw waveforms stay on site. Features, alerts, health summaries may leave to approved destinations. |
| Change control | Change request 2 weeks ahead; changes in the monthly window (second Sunday). Standard changes possible if documented with rollback. |
| Control systems | No writes to PLCs or the historian. Read-only historian access via the OPC UA gateway. |
| Accounts | Site AD accounts only; no shared accounts; service accounts need an owner. |
| Hardware | Gateways must be fanless, 24 VDC, DIN-rail; no USB storage allowed after commissioning. |
| Support | Plant IT supports Windows and Linux servers in level 3; nobody on site writes Python today, but the reliability team has one analyst who uses notebooks. |
