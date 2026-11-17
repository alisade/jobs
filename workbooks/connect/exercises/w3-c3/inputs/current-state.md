# LFG telephony current state (as of 2026-10-09)

- Avaya Aura Communication Manager 8.1 (duplex, Ashburn) + Session Manager pair (Ashburn,
  Dallas) + Avaya SBCE (Ashburn A/B, Dallas DR). Help desk runs on vectors/VDNs and skills
  (EAS). 380 help desk agents (210 onshore, 120 Pune offshore, 50 Monterrey nearshore).
- Carriers: Lumen (toll-free RespOrg for 1-800-555-0142, SIP trunks into the Ashburn SBCE),
  Verizon (NY DIDs, PRI + SIP), AT&T (Chicago DIDs, PRI into a Chicago G450 gateway),
  Bell Canada (Toronto DID, PRI), BT (London DID into Genesys Engage).
- Lumen SIP trunk contract ends 2027-03-31. Avaya CM support renewal decision due 2027-06.
- Genesys Engage (London) handles UK help desk voice and all help desk chat. Five9 runs
  outbound outage notifications.
- The Chime SDK Voice Connector trunk (w3-c2) replaces the Lumen SIP trunk for the
  back-office Avaya users only.
- Amazon Connect Customer instance lfg-helpdesk-prod in us-east-1 with an ACGR replica in
  us-west-2 planned (ACGR requires numbers ported to Connect). SAML via Okta.
- Context today: the Avaya IVR collects the employee ID and passes it to agents via
  vector variables and the Avaya Workspaces screen; ServiceNow screen pop via Avaya AES CTI.
